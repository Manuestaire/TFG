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
import os
import time
import copy


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
    def bid(self, private_information, public_information):

        df_players = pd.DataFrame(public_information['players']).squeeze()
        public_info = copy.deepcopy(public_information)
        del public_info['players']
        public_info = pd.Series(public_info)

        row_df= pd.concat([public_info,df_players]).to_frame().T
#hacer dos series y: https://stackoverflow.com/questions/38109102/combining-two-series-into-a-dataframe-row-wise

        self.game_df = self.game_df.append(row_df,ignore_index=True)
        ##self.df = self.df.insert(-1,value=df_players)
        #self.df = self.df.append(df_players,ignore_index=True)
        #self.df = pd.concat([self.df,df_players],axis=1)

        launch=False

        return 4, launch

    def join_launch(self, private_information, public_information):
        print("JOIN LAUNCH?")
        return True

    def begin(self, private_information, public_information):
        print("GAME ABOUT TO BEGIN!!")
        for root, dirs, filenames in os.walk('./data'):
            for name in filenames:
                if(name.endswith('.csv')):
                    path = root+'/'+name
                    print(path)
                    file_df = pd.read_csv(path,sep=';')
                    file_df.head()
                    self.bd_df = pd.concat([self.bd_df,file_df],axis=0,ignore_index=True)
                    self.bd_df.to_csv('result_db.csv',sep=';')
                else:
                    print("UNKNOWN FILE EXT:"+root+'/'+name)

    def end(self, private_information, public_information):
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
        amount = min(private_information['bankroll'], public_information['last_winning_bid'] - 1)
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

