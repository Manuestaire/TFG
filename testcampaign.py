import os
import time
from runprocessing import *
import pandas as pd
import matplotlib.pyplot as plt

import operator

players={
    'OptimizationResult':["TemplateStrategy('","',0.33,0.63,0.628,-0.142)"],
    'Sample1'           :["TemplateStrategy('","',0.313,0.764,0.613,0.09)"],
    'Sample2'           :["TemplateStrategy('","',0.298,0.984,0.697,-0.12)"],
}

head='''
from strategies import *
from modelstrategy import TemplateStrategy

# Define players here.

player_dict = {
    '''
default_players=''''SpongeBob' : SpongeBob(),
    'PassiveLauncher' : PassiveLauncher(),
    'AlwaysLauncher' : AlwaysLaunch(),
    'AggressiveLauncher' : AggressiveLauncher(),
    'Evie' : EVBot(),
    '''
foot='''
}'''

cmap=plt.cm.get_cmap('tab10')
colors={
    'OptimizationResult':cmap(0),
    'Manu'              :cmap(0),
    'Sample1'           :cmap(1),
    'Sample2'           :cmap(2),
    'Evie'              :cmap(3),
    'SpongeBob'         :cmap(5),
    'PassiveLauncher'   :cmap(6),
    'AlwaysLauncher'    :cmap(4),
    'AggressiveLauncher':cmap(7),
}

def main():

    dictresults={}

    filedata=head+default_players

    write_results=True
    for name1,player1 in players.items():
        string1="'"+name1+"':"+player1[0]+name1+player1[1][:-1]+','+str(write_results)+player1[1][-1]
        if write_results:
            write_results=False
        filedata+=string1+''',
    '''
    filedata+=foot

    with open('players_rc.py','w+') as file:
        file.write(filedata)


    dictresults = runversus()
    print(dictresults)

    testresult=pd.DataFrame.from_dict(dictresults,orient='index')
    testresult.to_csv('testcampaign_'+time.strftime("%Y%m%d_%H%M%S")+'_results.csv',sep=';')

    original=''
    with open('players_rc_original.py','r') as file:
        original=file.read()
    with open('players_rc.py','w+') as file:
        file.write(original)

    # plt.pie(dictresults.values(),labels=dictresults.keys())
    # plt.show()
    plotpie(dictresults)

def plotpie(dictresults):
    # plt.figure()
    sorted_results=dict(sorted(dictresults.items(), key=operator.itemgetter(1),reverse=True))
    if 'OptimizationResult' in sorted_results.keys():
        explode_index=list(sorted_results.keys()).index('OptimizationResult')
    else:
        explode_index=list(sorted_results.keys()).index('Manu')
    explodes= [0.01]*len(sorted_results)
    explodes[explode_index]=0.05
    fig1, ax1 = plt.subplots()
    _, _, autopcts = ax1.pie(sorted_results.values(),explode= explodes, labels=sorted_results.keys(),labeldistance=None,
            autopct=lambda p: ('{:.1f}%'.format(p)) if p > 0 else '',
            shadow=False,startangle=90,
            colors=[colors[v] for v in sorted_results.keys()])

    plt.legend(loc=1,fontsize=12)

    plt.setp(autopcts, **{'weight':'bold', 'fontsize':12})

    # plt.show()




def runversus(multiprocess_run=True):
    ## primero escribo parámetros a archivo
    timestr = time.strftime("%Y%m%d_%H%M%S")
    basedir = "./data/campaign_"
    outdir = basedir+timestr+'_test'
    # if not os.path.exists(outdir):
    #     os.mkdir(outdir)
    char = 'a'
    while os.path.exists(outdir):
        outdir = basedir+'_'+char
        char = chr(ord(char) + 1)
    os.mkdir(outdir)

    ## Vuelco parámetros a csv
    filepath='campaigndata.csv'


    data=[timestr+'_test']
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
        multiprocess3(2000)
    else:
        singleprocess()

    ## luego analizo la función objetivo:
    ret=getWinChances(outdir)
    return ret


def getWinChances(outdir):
    frames=[]
    for root, dirs, filenames in os.walk(outdir):
        for name in filenames:
            if(name.endswith('.csv')):
                try:
                    path = root+'/'+name
                    # print(path)
                    file_df = pd.read_csv(path,sep=';',index_col=0,warn_bad_lines=False)
                    # file_df.columns = file_df.columns.str.replace(" ", "")
                    frames.append(file_df) #array de dataframes
                except Exception:
                    print('Error al leer archivo ',path)
            else:
                print("UNKNOWN FILE EXTENSION:"+root+'/'+name)

    playerdict=None
    if (len(frames)>0):
        players=frames[0].iloc[-1,frames[0].columns.get_loc('base_reward')+1:frames[0].columns.get_loc('tech')]
        playerdict=dict.fromkeys(players.index.values,0)
        for frame in frames:
            players=frame.iloc[-1,frame.columns.get_loc('base_reward')+1:frame.columns.get_loc('tech')].infer_objects()
            winner= players.idxmax()

            if winner in playerdict:
                playerdict[winner] += 1
            else:
                playerdict[winner] = 1

    return playerdict


if __name__ == "__main__":
    # plotpie(getWinChances('testdata\campaign_20210709_220945_test')) #Only OptimizationResult
    # plotpie(getWinChances('testdata\campaign_20210709_225024_test')) # + Sample 1 v2
    # plotpie(getWinChances('testdata\campaign_20210710_004920_test'))  # + Sample 2
    # plotpie(getWinChances('testdata\campaign_20210709_234217_test'))  # + Sample 1 + Sample 2
    plotpie(getWinChances('serverdata\campaign_20210712_002745')) #after reoptimize

    plt.show()
    # plotpie(getWinChances('data\campaign_20210710_015044'))
    # plotpie(getWinChances('data\campaign_20210710_104758'))
    # main()
