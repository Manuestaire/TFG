import subprocess
import time
import os
import signal
import math
import pandas as pd
from scipy.optimize import minimize

def multiprocess():
    games=500
    concurent_process=8
    p = [None]*concurent_process
    files = [None]*concurent_process
    for j in range(int(round(games/concurent_process,0))):
        for i in range(concurent_process):
            # try:
            #     out = subprocess.run("python smp.py", check=True, shell=True)
            #     print(out)
            # except Exception as e:
            #     print("EXCEPTION: "+e)
            # files[i]=open('log'+str(i),'w')
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
    frames=[]
    for root, dirs, filenames in os.walk(outdir):
        for name in filenames:
            if(name.endswith('.csv')):
                try:
                    path = root+'/'+name
                    # print(path)
                    file_df = pd.read_csv(path,sep=';',index_col=0)                    
                    # file_df.columns = file_df.columns.str.replace(" ", "")
                    frames.append(file_df) #array de dataframes
                except Exception:
                    print('Error al leer archivo ',path)
            else:
                print("UNKNOWN FILE EXTENSION:"+root+'/'+name)
    # obj = 0
    won_games=0
    games_in_campaign=0
    list=[]
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
                won_games+= int(rounds_till_end==0 and money_diff==0)
                # obj=won_games/games_in_campaign

            # z = 0
            # if aux.size!=0:
            #     z=201-aux.iloc[0] # positivo, mayor cuanto antes nos hayan eliminado
            # else:
            #     z=(frame.loc[frame.index[-1],"SpongeBob":"Evie"].values.max()-frame['Manu'].iloc[-1].item())/200 #0 si soy yo // positivo estoy por detrás (maximizo la distancia con el segundo)
            #     if math.isnan(z):
            #         z=(frame.loc[frame.index[-2],"SpongeBob":"Evie"].values.max()-frame['Manu'].iloc[-2].item())/200 #workaround para evitar NaN
            # if not math.isnan(z):
            #     obj+=z
            #     games_in_campaign+=1
            list.append(1-(won_games/games_in_campaign))
        stats=pd.Series(list[150:])
        cma150=stats.expanding(min_periods=25).mean()
        # print('sma:'+str(sma25.iloc[-1]))
        print(won_games/games_in_campaign)
        df.iloc[-1,-1]=cma150.iloc[-1]
        df.to_csv(filepath,sep=';')
    return cma150.iloc[-1]


def main():
    try:
        print("Hello World!")
        #### SIGNAL HANDLERS ####
        signal.signal(signal.SIGINT, prepare_exit)
        signal.signal(signal.SIGTERM, prepare_exit)

        initial_guess=[0.5,0.5,0.5,0.5]
        boundaries=((0,1),(0,1),(0,1),(0,1))
        res=minimize(runcampaign,x0=[initial_guess],bounds=boundaries,options={"maxiter":4})
        print(res)
    finally:
        prepare_exit()
        


def prepare_exit():
    if os.path.exists('campaigndata.csv'):
            os.rename('campaigndata.csv','campaigndata_'+time.strftime("%Y%m%d_%H%M%S")+'.csv')

if __name__ == "__main__":
    main()



        


                
            

