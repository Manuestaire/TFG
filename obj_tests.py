import subprocess
import time
import os
import signal
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import scipy.signal as sgn


def multiprocess():
    games=1000
    concurent_process=8
    p = [None]*concurent_process
    files = [None]*concurent_process
    for j in range(int(round(games/concurent_process,0))):
        print("batch:"+str(j))
        for i in range(concurent_process):
            # try:
            #     out = subprocess.run("python smp.py", check=True, shell=True)
            #     print(out)
            # except Exception as e:
            #     print("EXCEPTION: "+e)
            files[i]=open('log'+str(i),'w')
            try:
                # p[i]=subprocess.Popen(["python","smp.py"],stdout=files[i],stderr=files[i])
                p[i]=subprocess.Popen(["python","smp.py"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                time.sleep(0.01)
            except Exception as e:
                print("EXCEPTION: "+e)
            # else:
            #     print("Finished RUN")
        status = [None]*concurent_process
        while None in status:
            for i in range(concurent_process):
                # print('process '+str(i)+': '+str(status[i]))
                status[i]=p[i].poll()
            # time.sleep(5)
        for process in p:
            process.wait()

def singleprocess():
    for i in range(50):
        try:
            out = subprocess.run("python smp.py", check=True, shell=True)
            print(out)
        except Exception as e:
            print("EXCEPTION: "+e)
    else:
        print("Finished RUN")

def runcampaign(params,multiprocess_run=True):
    ## primero escribo parámetros a archivo
    timestr = time.strftime("%Y%m%d_%H%M%S")
    basedir = "./data/campaign_"
    outdir = basedir+timestr
    # if not os.path.exists(outdir):
    #     os.mkdir(outdir)
    char = 'a'
    while os.path.exists(outdir):
        outdir = basedir+timestr+'_'+char
        char = chr(ord(char) + 1)
    os.mkdir(outdir)
    
    ## Vuelco parámetros a csv
    filepath='campaigndata.csv'

    data=[timestr, params[0], params[1], params[2], params[3],0]
    row=pd.Series(data,index=['date','joindecision_threshold','launchdecision_threshold','raisebid_factor','risk_factor','objective'])
    df = None
    if os.path.exists(filepath):
        print('Saving to existing file')
        df = pd.read_csv(filepath,sep=';',index_col=0)
        df = df.append(row.to_frame().T,ignore_index=True) 
    else:
        df = row.to_frame().T
    df.to_csv(filepath,sep=';')

    ## luego corro la campaña
    if multiprocess_run:
        multiprocess()
    else:
        singleprocess()

    ## luego analizo la función objetivo:
    generate_stats(outdir)
    

def generate_stats(outdir):
    frames=[]
    for root, dirs, filenames in os.walk(outdir):
        for name in filenames:
            if(name.endswith('.csv')):
                try:
                    path = root+'/'+name
                    print(path)
                    file_df = pd.read_csv(path,sep=';',index_col=0,warn_bad_lines=False)                    
                    # file_df.columns = file_df.columns.str.replace(" ", "")
                    frames.append(file_df) #array de dataframes
                except Exception:
                    print('Error al leer archivo ',path)
            else:
                print("UNKNOWN FILE EXTENSION:"+root+'/'+name)
    stats_file = 'stats.csv'
    
    obj_cum = 0
    games_in_campaign=0

    cum_rounds_till_end = 0
    cum_money_diff=0
    cum_won_games=0

    row_list=[]

    if (len(frames)>0):
        #aux[aux['AggressiveLauncher']<0]['round'].iloc[0] #pilla la ronda en la que entra en bancarrota
        for frame in frames:
            aux = frame.loc[frame['Manu']<0,'round']
            if aux.size!=0:
                rounds_till_end=201-aux.iloc[0] # positivo, mayor cuanto antes nos hayan eliminado
            else:
                rounds_till_end=0
            
            money_diff=(frame.loc[frame.index[-1],"SpongeBob":"Evie"].values.max()-frame['Manu'].iloc[-1].item())/200 #0 si soy yo // positivo estoy por detrás (maximizo la distancia con el segundo)
            if math.isnan(money_diff):
                money_diff=(frame.loc[frame.index[-2],"SpongeBob":"Evie"].values.max()-frame['Manu'].iloc[-2].item())/200 #workaround para evitar NaN


            if not (math.isnan(rounds_till_end) or math.isnan(money_diff)):
                games_in_campaign+=1
                
                cum_money_diff+=money_diff
                cum_rounds_till_end+=rounds_till_end

                cum_won_games+= int(rounds_till_end==0 and money_diff==0)
                obj_cum+= money_diff if aux.size==0 else rounds_till_end
                # obj_value=obj_cum/games_in_campaign
                row = {
                    "num_games"     : games_in_campaign,
                    "rounds_till_end": cum_rounds_till_end/games_in_campaign,
                    "money_diff"    : cum_money_diff/games_in_campaign,
                    "win_percent"   : cum_won_games/games_in_campaign,
                    "obj_value"     : obj_cum/games_in_campaign,
                    }
                row_list.append(row)



        stats=pd.DataFrame(row_list)
        #write to file
        stats.to_csv(stats_file,sep=';')
        #plot
        plt.plot(stats['num_games'],stats.drop('num_games',axis=1))
        plt.legend(stats.columns.tolist()[1:])
        
        plt.figure()
        plt.plot(stats['num_games'],stats['win_percent'],'o--')
        filtered=sgn.savgol_filter(stats['win_percent'],101,0)
        filtered1=sgn.savgol_filter(stats['win_percent'],101,1)
        filtered2=sgn.savgol_filter(stats['win_percent'],101,2)
        filtered3=sgn.savgol_filter(stats['win_percent'],101,3)
        
        plt.plot(stats['num_games'],filtered)
        plt.plot(stats['num_games'],filtered1)
        plt.plot(stats['num_games'],filtered2)
        plt.plot(stats['num_games'],filtered3)
        plt.legend(['sample','0 degree','1st degree','2nd degree','3rd degree'])
        plt.figure()
        modes = ['full', 'same', 'valid']
        for m in modes:
            plt.plot(np.convolve(stats['win_percent'].to_numpy(), np.ones(50)/50, mode=m))
        plt.plot(stats['num_games'],stats['win_percent'],'o--')
        plt.legend(modes+['sample'])
        plt.grid(True,which='both')
        plt.figure()
        plt.plot(stats['num_games'],stats['win_percent'],'o--')
        windows=[26,50,100]
        for window in windows:
            aux=np.convolve(stats['win_percent'].to_numpy(), np.ones(window)/window, mode='valid')
            plt.plot(range(int(window/2),int(len(aux)+window/2)),aux)
        plt.grid(True,which='both')
        plt.legend(['sample']+ windows)
        plt.figure()
        plt.plot(stats['num_games'],stats['win_percent'],'o--')
        sma=stats.loc[:,'win_percent'].rolling(window=10).mean()
        sma25=stats.loc[:,'win_percent'].rolling(window=25).mean()
        sma50=stats.loc[:,'win_percent'].rolling(window=50).mean()
        sma100=stats.loc[:,'win_percent'].rolling(window=100).mean()
        plt.plot(stats['num_games'],sma)
        plt.plot(stats['num_games'],sma25)
        plt.plot(stats['num_games'],sma50)
        plt.plot(stats['num_games'],sma100)
        df=stats.loc[:,'win_percent']
        cma=df.expanding(min_periods=10).mean()
        plt.plot(stats['num_games'],cma)
        ema=df.ewm(span=25,adjust=False).mean()
        plt.plot(stats['num_games'],ema)
        plt.legend(['sample','SMA 10','SMA 25','SMA 50','SMA 100','CMA','EMA 25'])
        plt.figure()
        plt.plot(stats['num_games'],stats['win_percent'],'o--')
        cma=df.expanding(min_periods=25).mean()
        cma25=(df.iloc[25:]).expanding(min_periods=25).mean()
        cma50=(df.iloc[50:]).expanding(min_periods=25).mean()
        cma100=(df.iloc[100:]).expanding(min_periods=25).mean()
        cma150=(df.iloc[150:]).expanding(min_periods=25).mean()
        plt.plot(stats['num_games'],cma)
        plt.plot(range(25,25+len(cma25)),cma25)
        plt.plot(range(50,50+len(cma50)),cma50)
        plt.plot(range(100,100+len(cma100)),cma100)
        plt.plot(range(150,150+len(cma150)),cma150)
        plt.legend(['sample','CMA','CMA 25*','CMA 50*','CMA 100*','CMA 150*'])
        plt.show()


def main():
    try:
        print("Hello World!")
        #### SIGNAL HANDLERS ####
        signal.signal(signal.SIGINT, prepare_exit)
        signal.signal(signal.SIGTERM, prepare_exit)
        
        generate_stats("D:\Bibliotecas\Documentos\python\Space-mining-poker-master\data\campaign_20210605_024635")
        # generate_stats("D:\Bibliotecas\Documentos\python\Space-mining-poker-master\data\campaign_20210605_030229")
        # runcampaign([0.5,0.5,0.5,0.5])
    except Exception as e:
        print(e)
    finally:
        prepare_exit()
        


def prepare_exit():
    if os.path.exists('campaigndata.csv'):
            os.rename('campaigndata.csv','campaigndata_'+time.strftime("%Y%m%d_%H%M%S")+'.csv')

if __name__ == "__main__":
    main()



        


                
            

