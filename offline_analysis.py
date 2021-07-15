import numpy
from numpy.core.fromnumeric import mean
import pandas as pd
import matplotlib.pyplot as plt
import os
import math
from scipy import stats

from aux_functions import *

class paramData:
    """"Class wrapper for analysis data returned by the analysis"""
    passive_tech: tuple
    bid_tech: tuple

    base_reward_data: lognormData = None
    mining_payoff_data: lognormData = None
    t_stat: float = None
    crit_value: float = None
    p_value: float = None

    def __init__(self, passive:tuple, bid:tuple, base_reward_data:lognormData, payoff_data:lognormData, ttest:tuple):
        self.passive_tech = passive
        self.bid_tech = bid
        self.base_reward_data=base_reward_data
        self.mining_payoff_data=payoff_data
        self.t_stat = ttest[0]
        self.crit_value = ttest[1]
        self.p_value = ttest[2]

    def to_series(self):
        data=[getTimeNow(), self.passive_tech, self.bid_tech, self.base_reward_data.mean, self.base_reward_data.var, self.base_reward_data.loc, \
        self.mining_payoff_data.mean, self.mining_payoff_data.var, self.mining_payoff_data.loc, self.t_stat, self.crit_value, self.p_value]
        df=pd.Series(data,index=['date','passive_tech','bid_tech','base_reward_mean','base_reward_variance', 'base_reward_location', \
        'mining_payoff_mean','mining_payoff_variance', 'mining_payoff_location','t_stat','critical_value','p_value'])
        return df

    def to_file(self, tag:str = ''):
        timestr = time.strftime("%Y%m%d_%H%M%S")
        outdir = "./analysis"
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        filepath=outdir+'/'+tag+'_results.csv'
        if os.path.exists(filepath):
            print('Saving to: '+filepath)
            df = pd.read_csv(filepath,sep=';',index_col=0)
            df = df.append(self.to_series().to_frame().T,ignore_index=True)
        else:
            print('doesn\'t exists')
            df = self.to_series().to_frame().T
        df.to_csv(filepath,sep=';')


class offlineAnalysis:
    old_sample = pd.DataFrame()
    new_sample = pd.DataFrame()
    complete_sample = pd.DataFrame()

    def __init__(self):
        filename_list=[]
        for root, dirs, filenames in os.walk('./data'):
            for name in filenames:
                if(name.endswith('.csv')):
                    path = root+'/'+name
                    filename_list.append(path)
                else:
                    print("UNKNOWN FILE EXT:"+root+'/'+name)
        frames=[]
        for filename in filename_list[-2000:]:
            try:
                # print(filename)
                file_df = pd.read_csv(filename,sep=';',index_col=0)                    
                file_df.columns = file_df.columns.str.replace(" ", "")
                frames.append(file_df)
                print(filename)
            except Exception as e:
                print('Error al leer archivo ',filename)
                print(e)

        if (len(frames)>0):
            self.complete_sample = pd.concat(frames[-2000:])
            self.old_sample= pd.concat(frames[:100]) 
            self.new_sample= pd.concat(frames[-100:])

        self.complete_sample.to_csv('result_db.csv',sep=';')
        print("NO MORE FILES TO PARSE")


def analyze(sample_df : pd.DataFrame, show_figures=True, old_sample=numpy.array([]), new_sample=numpy.array([])):
        print("OFFLINE ANALYSYS RUNNING!!")
        
        if sample_df.size > 0 :
            # we need to drop the values where the round does not advance
            #(self.sample_df.loc[self.sample_df['auction_round']==1])['last_mining_payoff'].mean()
            ar=sample_df.loc[sample_df['auction_round']==1]
            ###### BEGIN base_reward ######
            base_reward=ar['base_reward'].dropna()
            br_bins=numpy.arange(-1,base_reward.max())+0.5
            base_reward.hist(bins=br_bins, density=True) 
            
            #parametric estimation
            r_mean,r_var=lognorm_estimate(base_reward)
            print('base_reward mean:'+str(r_mean)+' var:'+str(r_var))
            
            #plot
            #p_range=numpy.linspace(-1,base_reward.max(),base_reward.max()*2)
            r_range=numpy.concatenate((numpy.linspace(0,math.floor(base_reward.max()/2),int(base_reward.max()*2)),numpy.linspace(math.ceil(base_reward.max()/2),base_reward.max())))
            r_dist=stats.lognorm(r_var,scale=numpy.exp(r_mean))
            rshape,rloc,rscale = stats.lognorm.fit(base_reward)
            r_mean2=numpy.log(rscale)
            r_dist2=stats.lognorm.pdf(r_range,rshape,loc=rloc,scale=rscale)
            plt.plot(r_range,r_dist.pdf(r_range))
            plt.plot(r_range,r_dist2)
            plt.title('base_reward') 
            plt.legend(['basic parametric estimation','scipy-fit (with location)'])
            plt.xlabel('x')
            plt.ylabel('f(x)')
            plt.show(block=False)
            baser_mean=r_mean2
            baser_var=rshape
            base_reward_data=lognormData(r_mean2,rshape,rloc)
            br_expect=r_dist.expect()

            ttest_result=[numpy.NaN,numpy.NaN,numpy.NaN]
            if(old_sample.size>0 and new_sample.size>0):
                ttest_result=TTest(old_sample['tech_gain_passive'].dropna(),new_sample['tech_gain_passive'].dropna()) #TODO!
            ###### END base_reward ######

            ###### BEGIN mining_payoff ######
            # PLOT histograma:
            plt.figure()
            mining_payoff=ar['last_mining_payoff'].dropna()
            payoff_bins=numpy.arange(-1,mining_payoff.max())+0.5
            mining_payoff.hist(bins=payoff_bins,density=True) 
            payoff_hist = numpy.histogram(mining_payoff, bins=payoff_bins, density=True)
            payoff_cdf=numpy.cumsum(payoff_hist[0])

            
            # PLOT pdf options
            p_mean,p_var=lognorm_estimate(mining_payoff)
            print('mining_payoff mean:'+str(p_mean)+' var:'+str(p_var))
            p_range=numpy.linspace(-1,int(mining_payoff.max()),int(mining_payoff.max()*2))
            #numpy.concatenate((numpy.linspace(0,math.floor(mining_payoff.max()/2),int(mining_payoff.max()*2)),numpy.linspace(math.ceil(mining_payoff.max()/2),mining_payoff.max())))
            p_dist=stats.lognorm.pdf(p_range,p_var,scale=numpy.exp(p_mean))
            plt.plot(p_range,p_dist)
            
            
            shape,floc,fscale = stats.lognorm.fit(mining_payoff) #Note: [shape=sigma, scale=exp(mu)] (scipy docs)
            mean=numpy.log(fscale)
            payoff_data=lognormData(mean,shape,floc)

            p_mean2,p_var2=lognorm_estimate(mining_payoff-2)
            p_dist2=stats.lognorm.pdf(p_range,p_var2,scale=numpy.exp(p_mean2))
            plt.plot(p_range-2,p_dist2)
            p_dist3=stats.lognorm.pdf(p_range,shape,loc=floc,scale=fscale)
            plt.plot(p_range,p_dist3)

            payoff_distribution=stats.lognorm(shape,loc=floc,scale=fscale)
            x_axis=range(payoff_cdf.size)
            payoff_theor_cdf=payoff_distribution.cdf(x_axis) #!!mover!

            plt.title('mining payoff') 
            plt.legend(['basic parametric estimation','parametric with displacement','scipy-fit (with location parameter)']) 
            plt.xlabel('x')
            plt.ylabel('f(x)')   
            plt.show(block=False)
            payoff_mean=mean
            payoff_var=shape

            # Test de Cramer von Mises
            t_ret = stats.cramervonmises(mining_payoff,payoff_distribution.cdf)
            t_val= cvmTest(mining_payoff,payoff_distribution.cdf)

            # PLOT cdf real y estimado
            plt.figure()
            base_reward_test=ar['base_reward'].dropna()
            # t_ret2 = stats.cramervonmises(base_reward_test,payoff_distribution.cdf)
            plt.plot(x_axis,payoff_cdf)
            plt.plot(x_axis,payoff_theor_cdf)
            plt.legend(['payoff cdf','parametric-estimated payoff cdf'])
            plt.xlabel('x')
            plt.ylabel('F(x)')
            plt.show(block=False)
            

            # PLOT base_reward<->payoff correlation
            plt.figure()
            correlation = (ar['base_reward'].shift(1)).corr(ar['last_mining_payoff'])
            print("base_reward to mining_payoff correlation:"+str(correlation))
            b = ar[['base_reward','last_mining_payoff']]
            plt.scatter(b['base_reward'].shift(1),b['last_mining_payoff'],s=1)
            plt.xlabel('base_reward')
            plt.ylabel('last_mining_payoff')
            plt.show(block=False)
            ###### END mining_payoff ######

            ###### BEGIN Failure chance ######
            # failure_rounds=sample_df.loc[sample_df['last_winning_miner']=='Mission failure']['round']
            failure_rounds=ar.loc[ar['last_winning_miner']=='Mission failure']['round']
            failure_rounds_arr=numpy.sort(failure_rounds)
            val,count = numpy.unique(failure_rounds_arr,return_counts=True)
            num_rounds=ar['round'].value_counts().reindex(val)
            plt.figure()
            plt.bar(val,count/num_rounds.values)
            plt.ylabel('f(x)')
            plt.xlabel('round #')
            plt.show(block=False)
            ###### END Failure chance ######


            ###### BEGIN calculate expected values ######
            #covariance=correlation*payoff_var*baser_var
            techreward_mean=payoff_mean-2*baser_mean
            techreward_var=payoff_var-4*baser_var

            ###### END calculate expected values ######
            

            ###### BEGIN won_tech ######
            # won_tech= self.sample_df['tech'] - self.sample_df['tech'].shift(1)  
            # corrected_won_tech= copy.deepcopy(won_tech)
            # corrected_won_tech[corrected_won_tech<0] = self.sample_df['tech'] #<-aquí tengo la tecnología ganada en mantenimiento cada ronda
            fig, ax = plt.subplots(1, 2,figsize=(12,5.4))
            won_tech_passive=sample_df['tech_gain_passive']
            won_tech_passive.dropna().hist(bins=numpy.arange(-1,11)+0.5,density=True,ax=ax[0])
            ax[0].set_title('tech_gain_passive')     
            
            won_tech_bid=sample_df['tech_gain_bid']
            won_tech_bid.dropna().hist(bins=numpy.arange(-1,11)+0.5,density=True,ax=ax[1])
            ax[1].set_title('tech_gain_bid') 
            plt.setp(ax[:], xlabel='x')
            plt.setp(ax[0], ylabel='f(x)')
            plt.show() if show_figures else plt.figure()
            ###### END won_tech ######



            return_data = paramData(getUniformParams(won_tech_passive),getUniformParams(won_tech_bid),base_reward_data,payoff_data,ttest_result) # ttest_result
            return_data.to_file()

            #new_df = pd.concat([won_tech,corrected_won_tech],axis=1) #debugging
            #corrected_won_tech.plot.density(ind=range(0,11))

            # shifted_df = self.sample_df[['last_winning_bid','last_winning_bidders']].shift(-1)
            #bid_won_tech= self.sample_df.loc['Manu' in shifted_df['last_winning_bidders']]
            #aux=(shifted_df['last_winning_bidders'].dropna().str.contains('Manu')).fillna(value=False)


        
            # (self.sample_df.loc[self.sample_df['tech']!=self.sample_df['tech_at_join']!=])['tech_at_join'].dropna().hist(bins='auto')
            # plt.figure(1)
        else:
            print('Could not generate BD_dataframe')



def main():
    analysis = offlineAnalysis()
    analyze(analysis.complete_sample,True,analysis.old_sample,analysis.new_sample)
    # TTest(['tech_gain_passive'].dropna(),analysis.new_sample['tech_gain_passive'].dropna())

if __name__ == "__main__":
    main()
