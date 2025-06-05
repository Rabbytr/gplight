from .base import BaseAgent
from .rl_agent import RLAgent
from .maxpressure import MaxPressureAgent

try:
    from .colight import CoLightAgent
    from .dqn import DQNAgent
    from .sotl import SOTLAgent
    from .frap import FRAP_DQNAgent
    from .ppo_pfrl import IPPO_pfrl
    # from .maddpg import MADDPGAgent
    # from .maddpg_v2 import MADDPGAgent
    from .presslight import PressLightAgent
    from .fixedtime import FixedTimeAgent
    from .mplight import MPLightAgent
except ModuleNotFoundError as ex:
    print(ex, end=' => ')
    print('DRL-based methods require the installation of `torch` and related modules')

from .gplight_plus import GPLightPlus
from .gplight import GPLight

# from .ppo_pfrl import IPPO_pfrl
