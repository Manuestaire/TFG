"""
modelstrategy.py

Estrategia modelo para la creación de estrategias con comportamientos dominantes por medio de los parámetros de decisión
"""
import numpy
import math
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import copy

from aux_functions import *
from offline_analysis import lognormData
from strategies import Strategy

class TemplateStrategy(Strategy):
    game_df = pd.DataFrame()
    players_tech_count = {}

    name=''

    br_expect=12.70805407824309 #TODO
    payoff_expect= 26.76786969043813 #TODO
    unkn_expect= payoff_expect - br_expect

    tech_cost = 5
    prev_tech = 0
    prev_bid = 2
    eliminated_player_count=0
    launched = False

    UPKEEP_COST= 5
    LAST_ROUND = 201
    TECH_EXPECTATION = 5

    campaign_folder = ''
    joindecision_threshold=0.5
    launchdecision_threshold=0.5
    raisebid_factor = 0.5
    risk_factor=0.5

    write_results=False

    def __init__(self, name:str, join_threshold, launch_threshold, raise_factor, risk_factor,write_results=False):
        self.name=name
        self.joindecision_threshold = join_threshold
        self.launchdecision_threshold = launch_threshold
        self.raisebid_factor = raise_factor
        self.risk_factor = risk_factor
        self.write_results = write_results

    def addRow(self, private_information, public_information):
        try:
            tech_gain = private_information['tech']-self.prev_tech if not self.launched else private_information['tech']
            
            players_dict={}
            for key,value in public_information['players'].items():
                players_dict[key]=value['bankroll']
            public_info = copy.deepcopy(public_information)
            del public_info['players']
            extend_dict={'tech':numpy.NaN,'tech_gain_passive':numpy.NaN,'tech_at_join':numpy.NaN,'tech_gain_bid':numpy.NaN}

            row_dict={**public_info,**players_dict,**extend_dict}
            row_df=pd.DataFrame.from_dict(row_dict,orient='index').T.infer_objects()
    
            row_df.at[0,'tech' if public_info['auction_round']<=1 else 'tech_at_join']=private_information['tech']
            #hacer dos series y: https://stackoverflow.com/questions/38109102/combining-two-series-into-a-dataframe-row-wise

            if public_info['auction_round']<=1:
                row_df.at[0,'tech_gain_passive']=tech_gain
            elif (self.name in public_information['last_winning_bidders']): 
                row_df.at[0,'tech_gain_bid']=tech_gain
        except Exception:
            print(self.name+': Error al generar fila en la ronda ',public_info['round'])
        self.game_df = self.game_df.append(row_df,ignore_index=True) #add row to game_df
        return row_df

    def bid(self, private_information, public_information):

        #### BEGIN CRONS ####
        self.addRow(private_information, public_information)
        self.tech_cost+=5
        
        eliminated_player_count=0
        if(public_information['auction_round']==1): #Hubo lanzamiento en la ronda anterior
            if(public_information['last_launchers'] != None):
                for launcher in public_information['last_launchers']:
                     self.players_tech_count[launcher]=0
            for player, data in public_information['players'].items():
                if(data['bankroll']<0):
                    eliminated_player_count+=1
                    self.players_tech_count[player]=0 #lo fuerzo a cero para evitar que influya en la toma de decision
                else:
                    self.players_tech_count[player]+=1
        #### END CRONS ####

        ## bid & launch decision: ##
        bid_amount=self.prev_bid
        launch=False
        
        player_tech_expected=copy.deepcopy(self.players_tech_count)
        player_tech_expected.update((k,v*self.TECH_EXPECTATION) for k,v in player_tech_expected.items()) 

        basereward_mod=numpy.sqrt((public_information['base_reward']/self.br_expect)+0.125)
        launch = (private_information['tech']/sum(player_tech_expected.values()))*basereward_mod > self.launchdecision_threshold #+failure_chance #and expected reward is greater than tech invested?
        if launch:
            self.tech_cost=0


        #cálculo de won_bids:
        counts=(self.game_df['last_winning_bidders'].tail(5).value_counts())
        i=0
        won_bids=0
        shared_wins=0
        for key,value in counts.iteritems():
            if self.name in key:
                won_bids+=value
                if key != [self.name]:
                    shared_wins+=value
        total_bids=sum(counts)

        #lógica de bid_amount:
        if((won_bids-shared_wins)/total_bids > (self.raisebid_factor * (max(len(self.players_tech_count),eliminated_player_count+1)/len(self.players_tech_count)))): #TODO: Rework (la intención era que el factor sea 1 cuando quedemos 2)
            bid_amount= min(math.ceil(self.prev_bid/2)+1,self.prev_bid-1)
        elif(self.name not in public_information['last_winning_bidders']):
            bid_amount=self.prev_bid+3
        elif([self.name]!=public_information['last_winning_bidders']):
            bid_amount=self.prev_bid+1 #si comparto la victoria sólo subo la apuesta lo mínimo
        else:
            bid_amount-=1 #si la gané yo sólo voy reduciendo de uno en uno

        bid_amount=max(0,bid_amount)

        
        if(self.tech_cost>(public_information['base_reward']+self.unkn_expect)*(self.risk_factor+0.5)):
            bid_amount=1

        ## Memory vars: ##
        self.launched=launch
        self.prev_tech=private_information['tech']
        self.prev_bid=bid_amount

        return min(private_information['bankroll'],bid_amount), launch

    def join_launch(self, private_information, public_information):
        #### BEGIN CRONS ####
        #actualizo el no. de veces que han conseguido tecnología los jugadores
        if(public_information['last_winning_bidders']!=None):
            for player in public_information['last_winning_bidders']:
                self.players_tech_count[player]+=1
        
        self.game_df.loc[self.game_df.index[-1],'tech_at_join']=private_information['tech'] #rellenamos el campo "tech_at_join"

        #si he ganado la puja actualizo el campo "last_winning_bid"
        if self.name in public_information['last_winning_bidders']:
            tech_gain_bid = private_information['tech'] - self.prev_tech
            self.tech_cost+=public_information['last_winning_bid']
            self.game_df.loc[self.game_df.index[-1],'tech_gain_bid']=tech_gain_bid

        #actualizo variables de memoria
        self.prev_tech=private_information['tech']
        #### END CRONS ####

        player_tech_expected=copy.deepcopy(self.players_tech_count)
        player_tech_expected.update((k,v*5) for k,v in player_tech_expected.items()) 
        
        basereward_mod=numpy.sqrt((public_information['base_reward']/self.br_expect)+0.125)
        joining_launch = (private_information['tech']/sum(player_tech_expected.values()))*basereward_mod > self.joindecision_threshold
        if joining_launch:
            self.tech_cost=0

        ## Memory vars: ##
        self.launched|=joining_launch

        return joining_launch

    def begin(self, private_information, public_information):
        self.players_tech_count = {p:0 for p in public_information['players'].keys()}

        filepath="campaigndata.csv"
        if os.path.exists(filepath):
            campaign_data = pd.read_csv(filepath,sep=';',index_col=0).iloc[-1]
            self.campaign_folder='/campaign_'+campaign_data['date']
    
        #### BEGIN Read persistent data from offline analysis ####
        filepath="./analysis/_results.csv"
        if os.path.exists(filepath):
            persistent_data = pd.read_csv(filepath,sep=';',index_col=0)
            distrib_data=persistent_data.iloc[-1]
            base_reward_dist=lognormData(distrib_data['base_reward_mean'],distrib_data['base_reward_variance'], distrib_data['base_reward_location'])
            payoff_dist = lognormData(distrib_data['mining_payoff_mean'],distrib_data['mining_payoff_variance'], distrib_data['mining_payoff_location'])

            # self.br_expect=base_reward_dist.distribution().expect()
            # self.payoff_expect= payoff_dist.distribution().expect()
            # self.unkn_expect=  self.payoff_expect -  self.br_expect
        else:
            print("ERROR: couldn't find persistance data from offline analysis")
        #### END Read persistent data ####

    def end(self, private_information, public_information):
        if self.write_results:
            self.addRow(private_information, public_information)

            timestr = time.strftime("%Y%m%d_%H%M%S")
            outdir = "./data"+self.campaign_folder
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            path = outdir+'/'+timestr+'_'+self.name+'_result.csv'
            char = 'b'
            while os.path.exists(path):
                path = outdir+'/'+timestr+'_'+self.name+'_'+char+'_result.csv'
                char = chr(ord(char) + 1)
            with open(path,"x",newline='') as file:
                print("saving to: "+path)
                self.game_df.to_csv(file,sep=';')
            print("END  OF THE GAME")

