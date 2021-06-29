"""
This file is meant to be modified to define the players active in the game.
"""

from strategies import *
from modelstrategy import TemplateStrategy

# Define players here.

player_dict = {
    # 'Sharma' : 'laika.clients.soton.ac.uk:49000',
    # 'Wittig' : 'localhost:49001',
    # 'Sivyer' : 'localhost:49229',
    # 'Simpson' : 'localhost:49193',
    # 'Peploe' : 'localhost:49823',
    # 'Comerford' : 'localhost:49902',
    # 'Freckelton' : 'localhost:49224',
    # 'Lovelock' : 'localhost:49933',
    #'Cedric' : Terminal(),
    'SpongeBob' : SpongeBob(),
    'PassiveLauncher' : PassiveLauncher(),
    'AlwaysLauncher' : AlwaysLaunch(),
    'AggressiveLauncher' : AggressiveLauncher(),
    'Manu' : Manu(),
    #'Observer' : Observer(),
    'Evie' : EVBot(),
    ##Template players:
    # 'Launcher':TemplateStrategy('Launcher',0.0,0.0,0,0),
    # 'Passive':TemplateStrategy('Passive',0.0,1.0,0.0,0.0),
    # 'Gambler':TemplateStrategy('Gambler',1.0,1.0,1.0,1.0),

}
