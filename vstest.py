import os
import time
from runprocessing import *
import pandas as pd
import math

def main():
    players={
        'Launcher'      :["TemplateStrategy('","',0.0,0.0,0,0)"],
        'Passive'       :["TemplateStrategy('","',0.0,1.0,0.0,0.0)"],
        'Equilibrated'  :["TemplateStrategy('","',0.5,0.5,0.5,0.5)"],
        'Gambler'       :["TemplateStrategy('","',0.5,0.5,1.0,1.0)"],
    }

    head='''
from strategies import *
from modelstrategy import TemplateStrategy

# Define players here.

player_dict = {
    '''
    foot='''
}'''

    dictresults={}
    for name1,player1 in players.items():
        string1="'"+name1+"':"+player1[0]+name1+player1[1][:-1]+',True'+player1[1][-1]
        results=[]
        for name2,player2 in players.items():
            name2+='2'
            string2="'"+name2+"':"+player2[0]+name2+player2[1]

            filedata=head+string1+''',
    '''+string2+','+foot
            with open('players_rc.py','w+') as file:
                file.write(filedata)

            results.append(runversus(name1,name2))
        dictresults[name1]=results

    
    vsresult=pd.DataFrame.from_dict(dictresults,orient='index',columns=players.keys())
    vsresult.to_csv('versus_results.csv',sep=';')

    original=''
    with open('players_rc_original.py','r') as file:
        original=file.read()
    with open('players_rc.py','w+') as file:
        file.write(original)    




def runversus(name1,name2,multiprocess_run=True):
    ## primero escribo parámetros a archivo
    timestr = time.strftime("%Y%m%d_%H%M%S")
    basedir = "./data/campaign_"
    outdir = basedir+timestr
    # if not os.path.exists(outdir):
    #     os.mkdir(outdir)
    char = 'a'
    while os.path.exists(outdir):
        outdir = basedir+name1+'VS'+name2+'_'+char
        char = chr(ord(char) + 1)
    os.mkdir(outdir)
    
    ## Vuelco parámetros a csv
    filepath='campaigndata.csv'


    data=[timestr]
    row=pd.Series(data,index=['date'])
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
        multiprocess2(1000)
    else:
        singleprocess()

    ## luego analizo la función objetivo:
    ret=getWinChance(name1,name2,outdir)
    return ret


def getWinChance(name1,name2,outdir):
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

    
    if (len(frames)>0):
    #aux[aux['AggressiveLauncher']<0]['round'].iloc[0] #pilla la ronda en la que entra en bancarrota
        games_in_campaign=0
        cum_won_games=0
        for frame in frames:

            money_diff=(frame.loc[frame.index[-1],name1:name2].values.max()-frame[name1].iloc[-1].item())/200 #0 si soy yo // positivo estoy por detrás (maximizo la distancia con el segundo)
            if math.isnan(money_diff):
                money_diff=(frame.loc[frame.index[-2],name1:name2].values.max()-frame[name1].iloc[-2].item())/200 #workaround para evitar NaN


            if not (math.isnan(money_diff)):
                games_in_campaign+=1

                cum_won_games+= int(money_diff==0)
                
                # obj_value=obj_cum/games_in_campaign
    return cum_won_games/games_in_campaign

if __name__ == "__main__":
    main()