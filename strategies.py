"""
strategies.py

Put all strategies in here and import into main file.

A strategy needs to implement .bid() and .join_launch() methods.

Optional methods are .begin() and .end() called at the start and
end of a game (or bankruptcy of the player), respectively, as
well as .broadcast(), which receives human readable messages
about the game's progress.
"""

# from ntpath import join
import numpy
import math
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import copy

from aux_functions import *
from random import random


class Strategy(object):
    """
    Template strategy, which specific strategies inherit.
    """
    def bid(self, private_information, public_information):
        raise Exception("you need to implement a bid strategy!")

    def join_launch(self, private_information, public_information):
        raise Exception("you need to implement a launch strategy!")

    def begin(self, private_information, public_information):
        pass

    def end(self, private_information, public_information):
        pass

    def broadcast(self, message):
        # assume bot, so no messages necessary
        pass

    def ping(self):
        return True

class Manu(Strategy):
    game_df = pd.DataFrame()
    players_tech_count = {}

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

    def addRow(self, private_information, public_information):
        try:
            tech_gain = private_information['tech']-self.prev_tech if not self.launched else private_information['tech']
            
            players_dict={}
            for key,value in public_information['players'].items():
                players_dict[key]=value['bankroll']
            public_info = copy.deepcopy(public_information)
            del public_info['players']
            extend_dict={'tech':numpy.NaN,'tech_gain_passive':numpy.NaN,'tech_at_join':numpy.NaN,'tech_gain_bid':numpy.NaN}

            try:
                if public_info['auction_round']<=1:
                    extend_dict['tech_gain_passive']=tech_gain
                elif ('Manu' in public_information['last_winning_bidders']): 
                    extend_dict['tech_gain_bid']=tech_gain

                extend_dict['tech' if public_info['auction_round']<=1 else 'tech_at_join']=private_information['tech']
            except Exception:
                print('Manu: Error menor al generar fila en la ronda ',public_info['round'])
            
            row_dict={**public_info,**players_dict,**extend_dict}
            row_df=pd.DataFrame.from_dict(row_dict,orient='index').T.infer_objects()
    
            #hacer dos series y: https://stackoverflow.com/questions/38109102/combining-two-series-into-a-dataframe-row-wise

        except Exception:
            print('Manu: Error al generar fila en la ronda ',public_info['round'])
        self.game_df = self.game_df.append(row_df,ignore_index=True) #add row to game_df
        # self.game_df = pd.concat([self.game_df,row_df],ignore_index=True,copy=False)
        return row_df

    def bidStrategy(self,public_information,private_information,riskfactor,optimismfactor):


        actual_expected_reward = public_information['base_reward']+self.unkn_expect #cuánto espero ganar del próximo meteorito
        total_spent=0 #TODO
        total_spent/public_information['round'] #compara con cuánto están gastando los demás (si les va bien les copio)
        public_information['last_mining_payoff']
        self.tech_cost
        private_information['tech'] #total tecnología actual

        #factores psicológicos:
        if( (actual_expected_reward) * optimismfactor > 2*self.payoff_expect):
            cs_er = max(actual_expected_reward, 2*self.payoff_expect * (1+optimismfactor))
        else:
            cs_er = actual_expected_reward * (0.5+optimismfactor)
        cr_es = max(self.br_expect,cs_er)

        #estimo cuánta tech tienen los demás jugadores:
        player_tech_expected=copy.deepcopy(self.players_tech_count)
        player_tech_expected.update((k,self.TECH_EXPECTATION*5) for k,v in player_tech_expected.items()) 
        for k,v in player_tech_expected.items():
            if(self.players_tech_count['Manu']>=2 and \
            v>2*private_information['tech']):
                player_tech_expected[k]=None #descarto a este jugador porque es demasiado conservador (puede ser un observador)
        player_tech_expected['Manu']=None # a mí también me descarto


        remaining_rounds= (self.LAST_ROUND-public_information['round'])  
        ps=remaining_rounds*(self.UPKEEP_COST) #coste de no lanzar hasta el final de partida
        pr=remaining_rounds*self.payoff_expect #total estimated price pool remaining
        total_spent = 0 #TODO_ total gastado a lo largo de la partida
        pr+private_information['bankroll']-(ps+total_spent)>0 #esto me dice si voy bien o mal



        if private_information['tech'] > max(player_tech_expected.values()): #quiero mantener la ventaja
            bid_amount = 5 
        #si gano esta puja debería lanzar o unirme
        
        launch=False
        if private_information['tech'] >= max(player_tech_expected.values())*(1-riskfactor): #TODO: modificar para que entre sobretodo al principio (me sale un 10 en la primera ronda) si la recompensa es baja no me interesa
            launch=True

        potential_profit=cr_es-(self.UPKEEP_COST+bid_amount)
        if potential_profit > 0:  # me sale rentable lanzar
            launch=True

        if public_information['round']==self.LAST_ROUND:
            launch=True

        if launch: #si me interesa lanzar seguramente quiera apostar
            if private_information['tech']+self.TECH_EXPECTATION > max(player_tech_expected.values()) and private_information['tech'] < max(player_tech_expected.values()): 
                bid_amount = min(cr_es,actual_expected_reward)-self.UPKEEP_COST #si con una puja espero superar la tech de los demás estoy dispuesto a pagar
            elif private_information['tech']  > max(player_tech_expected.values()) or  private_information['tech']<=2 :
                bid_amount = self.UPKEEP_COST #si ya estamos por delante pujamos el coste de mantenimiento
            else:
                bid_amount = min(self.game_df['last_winning_bid'].iloc[-1].min(),self.UPKEEP_COST)
        else: #no lanzamos este turno
            if private_information['tech']+self.TECH_EXPECTATION > max(player_tech_expected.values()) and private_information['tech'] < max(player_tech_expected.values()):
                bid_amount = min(self.game_df['last_winning_bid'].iloc[-1].min(),self.UPKEEP_COST)
            else:
                bid_amount = 1
            

        ## JOIN STRATEGY:
        join_launch=False
        if private_information['tech'] < player_tech_expected.values().min()*(1+riskfactor) or launch:
            join_launch = True
        elif actual_expected_reward < self.payoff_expect:
            join_launch = False
        else: 
            join_launch = private_information['tech'] < self.payoff_expect
        
            


        #a = min(max(self.br_expect,numpy.log(public_information['base_reward'])), self.payoff_expect) * confidencefactor # qué peso le damos a este factor (log -> quiero dar más peso si hay más dispersión)
        #b = max(0,(cr_es-self.tech_cost)) * riskfactor        # cuánto estamos dispuestos a perder
        #c = self.tech_cost * memoryfactor      #



        return



    

    def bid(self, private_information, public_information):

        #### BEGIN CRONS ####
        self.addRow(private_information, public_information)
        self.tech_cost+=5
        
        eliminated_player_count=0
        if(public_information['auction_round']==1): #Hubo lanzamiento en la ronda anterior
            if(public_information['last_launchers'] != None):
                # print('hola')
                for launcher in public_information['last_launchers']:
                     self.players_tech_count[launcher]=0
            for player, data in public_information['players'].items():
                if(data['bankroll']<0):
                    eliminated_player_count+=1
                    self.players_tech_count[player]=0 #lo fuerzo a cero para evitar que influya en la toma de decision
                else:
                    self.players_tech_count[player]+=1
        #### END CRONS ####


        ##self.df = self.df.insert(-1,value=df_players)
        #self.df = self.df.append(df_players,ignore_index=True)
        #self.df = pd.concat([self.df,df_players],axis=1)
        
        ## bid & launch decision: ##
        bid_amount=self.prev_bid
        launch=False
        
        player_tech_expected=copy.deepcopy(self.players_tech_count)
        player_tech_expected.update((k,v*self.TECH_EXPECTATION) for k,v in player_tech_expected.items()) 

        basereward_mod=numpy.sqrt((public_information['base_reward']/self.br_expect)+0.125)
        launch = (private_information['tech']/sum(player_tech_expected.values()))*basereward_mod > self.launchdecision_threshold #+failure_chance #and expected reward is greater than tech invested?
        if launch:
            self.tech_cost=0
            print('ELIJO LANZAR')


        #cálculo de won_bids:
        counts=(self.game_df['last_winning_bidders'].tail(5).value_counts())
        i=0
        won_bids=0
        shared_wins=0
        for key,value in counts.iteritems():
            if 'Manu' in key:
                won_bids+=value
                if key != ['Manu']:
                    shared_wins+=value
        total_bids=sum(counts)

        #lógica de bid_amount:
        if(self.tech_cost>(public_information['base_reward']+self.unkn_expect)*(self.risk_factor+0.5)):
            bid_amount=1
        elif((won_bids-shared_wins)/total_bids > (self.raisebid_factor * (max(len(self.players_tech_count),eliminated_player_count+1)/len(self.players_tech_count)))): #TODO: Rework (la intención era que el factor sea 1 cuando quedemos 2)
            bid_amount= min(math.ceil(self.prev_bid/2)+1,self.prev_bid-1)
        elif('Manu' not in public_information['last_winning_bidders']):
            bid_amount=self.prev_bid+3
        elif(['Manu']!=public_information['last_winning_bidders']):
            bid_amount=self.prev_bid+1 #si comparto la victoria sólo subo la apuesta lo mínimo
        else:
            bid_amount-=1 #si la gané yo sólo voy reduciendo de uno en uno

        bid_amount=max(0,bid_amount)


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
        if 'Manu' in public_information['last_winning_bidders']:
            tech_gain_bid = private_information['tech'] - self.prev_tech
            self.tech_cost+=public_information['last_winning_bid']
            self.game_df.loc[self.game_df.index[-1],'tech_gain_bid']=tech_gain_bid

        #actualizo variables de memoria
        self.prev_tech=private_information['tech']
        #### END CRONS ####

        print("JOIN LAUNCH?")

        player_tech_expected=copy.deepcopy(self.players_tech_count)
        player_tech_expected.update((k,v*5) for k,v in player_tech_expected.items()) 
        
        #joining_launch = (private_information['tech']/sum(player_tech_expected.values()))*(public_information['base_reward']/br_expect) > 0.4 #+failure_chance #and expected reward is greater than tech invested?
        
        basereward_mod=numpy.sqrt((public_information['base_reward']/self.br_expect)+0.125)
        joining_launch = (private_information['tech']/sum(player_tech_expected.values()))*basereward_mod > self.joindecision_threshold
        if joining_launch:
            self.tech_cost=0
            print('ELIJO UNIRME')

        #joining_launch=True
        ## Memory vars: ##
        self.launched|=joining_launch

        return joining_launch

    def begin(self, private_information, public_information):
        print("GAME ABOUT TO BEGIN!!")
        self.players_tech_count = {p:0 for p in public_information['players'].keys()}
        # for name in public_information['players'].keys():
        #     self.players_tech_count[name]=0

        #### carga campaña ####
        filepath="campaigndata.csv"
        if os.path.exists(filepath):
            campaign_data = pd.read_csv(filepath,sep=';',index_col=0).iloc[-1]
            self.campaign_folder='/campaign_'+campaign_data['date']
            self.joindecision_threshold = campaign_data['joindecision_threshold']
            self.launchdecision_threshold = campaign_data['launchdecision_threshold']
            self.raisebid_factor = campaign_data['raisebid_factor']
            self.risk_factor = campaign_data['risk_factor']

        #### BEGIN Read persistent data from offline analysis ####
        filepath="./analysis/_results.csv"
        if os.path.exists(filepath):
            persistent_data = pd.read_csv(filepath,sep=';',index_col=0)
            distrib_data=persistent_data.iloc[-1]
            base_reward_dist=lognormData(distrib_data['base_reward_mean'],distrib_data['base_reward_variance'], distrib_data['base_reward_location'])
            payoff_dist = lognormData(distrib_data['mining_payoff_mean'],distrib_data['mining_payoff_variance'], distrib_data['mining_payoff_location'])

            self.br_expect=base_reward_dist.distribution().expect()
            self.payoff_expect= payoff_dist.distribution().expect()
            self.unkn_expect=  self.payoff_expect -  self.br_expect
        else:
            print("ERROR: couldn't find persistance data from offline analysis")
        #### END Read persistent data ####

        #### READ PREVIOUS GAMES:
        if(random()<0.05): #due to performance reasons we only run fitness tests on 5% games
            filename_list=[]
            for root, dirs, filenames in os.walk('./data'):
                for name in filenames:
                    if(name.endswith('.csv')):
                        path = root+'/'+name
                        filename_list.append(path)
                    else:
                        print("UNKNOWN FILE EXT:"+root+'/'+name)
            frames=[]
            for filename in filename_list[-500:]:
                try:
                    print(filename)
                    file_df = pd.read_csv(filename,sep=';',index_col=0)                    
                    file_df.columns = file_df.columns.str.replace(" ", "")
                    frames.append(file_df)
                except Exception as e:
                    print('Error al leer archivo ',filename)
                    print(e)
            print("NO MORE FILES TO PARSE")

            if (len(frames)>0):
                #### BEGIN fitness tests ####
                sample_df=pd.concat(frames)
                mining_payoff=(sample_df['last_mining_payoff'].loc[sample_df['auction_round']==1]).dropna()
                t_stat = cvmTest(mining_payoff,payoff_dist.distribution().cdf)
                if(t_stat>0.46136):
                    print("Null hypothesis rejected, PAYOFF sample does not belong to given distribution")
                    payoff_bins=numpy.arange(-1,mining_payoff.max())+0.5
                    mining_payoff.hist(bins=payoff_bins,density=True) 
                    p_range=numpy.linspace(-1,int(mining_payoff.max()),int(mining_payoff.max()*2))
                    p_dist=payoff_dist.distribution().pdf(p_range)
                    # plt.plot(p_range,p_dist)
                    # plt.show()
                    # input("Press enter to continue")
                base_reward=(sample_df['base_reward'].loc[sample_df['auction_round']==1]).dropna()
                t_stat = cvmTest(base_reward,base_reward_dist.distribution().cdf)
                if(t_stat>0.46136):
                    print("Null hypothesis rejected, BASE REWARD sample does not belong to given distribution")
                    br_bins=numpy.arange(-1,base_reward.max())+0.5
                    base_reward.hist(bins=br_bins,density=True) 
                    p_range=numpy.linspace(-1,int(base_reward.max()),int(base_reward.max()*2))
                    p_dist=base_reward_dist.distribution().pdf(p_range)
                    # plt.plot(p_range,p_dist)
                    # plt.show()
                    # input("Press enter to continue")
                #### END fitness tests ####

    def end(self, private_information, public_information):
        self.addRow(private_information, public_information)
        # ax=None
        # self.game_df.loc[:,"SpongeBob":"Evie"].plot(ax=ax)
        # self.game_df[["round","auction_round"]].plot(ax=ax)
        # plt.show()
        timestr = time.strftime("%Y%m%d_%H%M%S")
        outdir = "./data"+self.campaign_folder
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        path = outdir+'/'+timestr+'_result.csv'
        char = 'b'
        while os.path.exists(path):
            path = outdir+'/'+timestr+'_'+char+'_result.csv'
            char = chr(ord(char) + 1)
        with open(path,"x",newline='') as file:
            print("saving to: "+path)
            self.game_df.to_csv(file,sep=';')
        print("END  OF THE GAME")



class Terminal(Strategy):
    """
    Human strategy always asks for input from terminal.
    """

    def bid(self, private_information, public_information):
        print('-------------')
        print(private_information['name'] + " up.")
        print(public_information)
        print("Your tech: %d" % private_information['tech'])
        print("Your money: %d" % private_information['bankroll'])
        amount = input("Enter bid: ")
        if not amount.isnumeric():
            amount = 0
        launch = input("Launch? (Y/N) ")
        if launch[0].upper() == 'Y':
            launching = True
        else:
            launching = False
        return int(amount), launching

    def join_launch(self, private_information, public_information):
        print('-------------')
        print(private_information['name'] + " up.")
        print(public_information)
        print("Your tech: %d" % private_information['tech'])
        print("Your money: %d" % private_information['bankroll'])
        launch = input("Join launch? (Y/N) ")
        if launch[0].upper() == 'Y':
            return True
        else:
            return False

    def broadcast(self, message):
        print(message)


class SpongeBob(Strategy):
    """
    SpongeBob always bids and launches based on fixed threshold.
    """

    def bid(self, private_information, public_information):
        amount = min(private_information['bankroll'], public_information['base_reward'])
        launching = private_information['tech'] > 10
        return amount, launching

    def join_launch(self, private_information, public_information):
        return private_information['tech'] > 15


class AlwaysLaunch(Strategy):
    """
    AlwaysLaunch never bids but always launches.
    """

    def bid(self, private_information, public_information):
        amount = 0
        launching = True
        return int(amount), launching

    def join_launch(self, private_information, public_information):
        return True


class PassiveLauncher(Strategy):
    """
    PassiveLauncher always lowball bids and launches when others do.
    """

    def bid(self, private_information, public_information):
        amount = min(private_information['bankroll'], round(public_information['last_winning_bid'] *0.9))
        launching = False
        #launching = numpy.random.uniform(0,1)>0.5
        return int(amount), launching

    def join_launch(self, private_information, public_information):
        return True


class Observer(Strategy):
    """
        Observer never joins the game but records all public information coming its way.
        It's not suitable for recording the full game as eventually it will run out of money.
        """
    
    def bid(self, private_information, public_information):
        return 0, False
    
    def join_launch(self, private_information, public_information):
        return False


class AggressiveLauncher(Strategy):
    """
    AggressiveLauncher always high bids and launches.
    """

    def bid(self, private_information, public_information):
        amount = min(private_information['bankroll'],
                     2 * public_information['last_winning_bid'])
        launching = True
        return int(amount), launching

    def join_launch(self, private_information, public_information):
        return False


class EVBot(Strategy):
    """
    EVBot sometimes bids and launches based on simple calculations of profitability.
    """

    def bid(self, private_information, public_information):
        launching = False
        # bid cheaper than base tech price
        amount = min(private_information['bankroll'], 2)
        # guess ev of launch
        # assume nobody carries over tech from previous round
        N = len(public_information['players'])
        p_win = max((private_information['tech'] / 10.0) ** N, 1.0)
        payoff = public_information['base_reward'] + 8 + numpy.sqrt(1.5 * 7 * N)
        ev = p_win * payoff
        # don't know why launching = (ev > 7) doesn't work?!
        if ev > 7:
            launching = True
        #print(N, private_information['tech'], payoff, p_win, ev, launching)
        return int(amount), launching

    def join_launch(self, private_information, public_information):
        return False

