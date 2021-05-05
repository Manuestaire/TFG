"""
strategies.py

Put all strategies in here and import into main file.

A strategy needs to implement .bid() and .join_launch() methods.

Optional methods are .begin() and .end() called at the start and
end of a game (or bankruptcy of the player), respectively, as
well as .broadcast(), which receives human readable messages
about the game's progress.
"""

import numpy
import pandas as pd
import matplotlib.pyplot as plt
import os
import time
import copy

from aux_functions import *


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
    bd_df = pd.DataFrame()
    players_tech_count = {}

    prev_tech = 0
    launched = False
    def addRow(self, private_information, public_information):
        tech_gain = private_information['tech']-self.prev_tech if not self.launched else private_information['tech']
        df_players = pd.DataFrame(public_information['players']).reset_index(drop=True)
        public_info = copy.deepcopy(public_information)
        del public_info['players']

        row=pd.DataFrame.from_dict(public_info,orient='index').T.infer_objects()
        row_df= pd.concat([row,df_players],axis=1)


        row_df.at[0,'tech' if public_info['auction_round']<=1 else 'tech_at_join']=private_information['tech']
        #hacer dos series y: https://stackoverflow.com/questions/38109102/combining-two-series-into-a-dataframe-row-wise

        row_df.at[0,'tech_gain_passive' if public_info['auction_round']<=1 else 'tech_gain_bid']=tech_gain
        self.game_df = self.game_df.append(row_df,ignore_index=True) #add row to game_df
        return row_df

    def bid(self, private_information, public_information):

        self.addRow(private_information, public_information)
        
        if(public_information['auction_round']==1): #Hubo lanzamiento en la ronda anterior
            if(public_information['last_launchers'] != None):
                # print('hola')
                for launcher in public_information['last_launchers']:
                     self.players_tech_count[launcher]=0
            for player, data in public_information['players'].items():
                if(data['bankroll']<0):
                    self.players_tech_count[player]=0 #lo fuerzo a cero para evitar que influya en la toma de decision
                else:
                    self.players_tech_count[player]+=1



        #self.bd_df.loc[self.bd_df.index[-2],'last_winning_bid']=5

        ##self.df = self.df.insert(-1,value=df_players)
        #self.df = self.df.append(df_players,ignore_index=True)
        #self.df = pd.concat([self.df,df_players],axis=1)

        launch=False

        #Memory vars:
        self.launched=launch
        self.prev_tech=private_information['tech']

        return 4, launch

    def join_launch(self, private_information, public_information):
        
        if(public_information['last_winning_bidders']!=None):
            for player in public_information['last_winning_bidders']:
                self.players_tech_count[player]+=1
        
        self.game_df.loc[self.game_df.index[-1],'tech_at_join']=private_information['tech']

        if 'Manu' in public_information['last_winning_bidders']:
            tech_gain_bid = private_information['tech'] - self.prev_tech
            self.game_df.loc[self.game_df.index[-1],'tech_gain_bid']=tech_gain_bid


        self.prev_tech=private_information['tech']
        print("JOIN LAUNCH?")

        joining_launch=True
        self.launched|=joining_launch

        return joining_launch

    def begin(self, private_information, public_information):
        print("GAME ABOUT TO BEGIN!!")
        self.players_tech_count = {p:0 for p in public_information['players'].keys()}
        # for name in public_information['players'].keys():
        #     self.players_tech_count[name]=0
        frames=[]
        for root, dirs, filenames in os.walk('./data'):
            for name in filenames:
                if(name.endswith('.csv')):
                    path = root+'/'+name
                    print(path)
                    file_df = pd.read_csv(path,sep=';',index_col=0)                    
                    file_df.columns = file_df.columns.str.replace(" ", "")
                    #self.bd_df = self.bd_df.append(file_df,ignore_index=True,sort=False)[file_df.columns.tolist()]
                    frames.append(file_df)
                else:
                    print("UNKNOWN FILE EXT:"+root+'/'+name)
        if (len(frames)>0):
            self.bd_df = pd.concat(frames)
        self.bd_df.to_csv('result_db.csv',sep=';')
        print("NO MORE FILES TO PARSE")

        if self.bd_df.size > 0 :
            # we need to drop the values where the round does not advance
            #(self.bd_df.loc[self.bd_df['auction_round']==1])['last_mining_payoff'].mean()
            #histograma:
            m_mean,m_var=lognorm_estimate((self.bd_df.loc[self.bd_df['auction_round']==1])['last_mining_payoff'].dropna())
            print('mining_payoff mean:'+str(m_mean)+' var:'+str(m_var))
            
            # won_tech= self.bd_df['tech'] - self.bd_df['tech'].shift(1)  
            # corrected_won_tech= copy.deepcopy(won_tech)
            # corrected_won_tech[corrected_won_tech<0] = self.bd_df['tech'] #<-aquí tengo la tecnología ganada en mantenimiento cada ronda
            won_tech_passive=self.bd_df['tech_gain_passive']
            won_tech_passive.dropna().hist(bins=numpy.arange(-1,11)+0.5,density=True)
            plt.title('tech_gain_passive')     
            # plt.show()
            won_tech_bid=self.bd_df['tech_gain_bid']
            won_tech_bid.dropna().hist(bins=numpy.arange(-1,11)+0.5,density=True)
            plt.title('tech_gain_bid') 
            # plt.show()

            #new_df = pd.concat([won_tech,corrected_won_tech],axis=1) #debugging
            #corrected_won_tech.plot.density(ind=range(0,11))

            # shifted_df = self.bd_df[['last_winning_bid','last_winning_bidders']].shift(-1)
            #bid_won_tech= self.bd_df.loc['Manu' in shifted_df['last_winning_bidders']]
            #aux=(shifted_df['last_winning_bidders'].dropna().str.contains('Manu')).fillna(value=False)


            (self.bd_df.loc[self.bd_df['auction_round']==1])['last_mining_payoff'].dropna().hist(bins='auto') 
            plt.title('mining payoff')     
            # plt.show()
            # (self.bd_df.loc[self.bd_df['tech']!=self.bd_df['tech_at_join']!=])['tech_at_join'].dropna().hist(bins='auto')
            # plt.figure(1)
            print('BD_dataframe generated successfully')
        else:
            print('Could not generate BD_dataframe')

    def end(self, private_information, public_information):
        self.addRow(private_information, public_information)
        timestr = time.strftime("%Y%m%d_%H%M%S")
        outdir = "./data"
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        self.game_df.to_csv(outdir+'/'+timestr+'_result.csv',sep=';')
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

