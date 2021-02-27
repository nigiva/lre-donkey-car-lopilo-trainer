import os
import sys

# For avoid warning in Visual Code
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from core.client import Client
from hardware.joystick import JoystickController
from controller import Controller
from brain.brain import Brain
from manager import DataManager

data_manager = DataManager("/home/nigiva/git/lopilo-trainer/data/")
data_manager.copy_model("/home/nigiva/git/lopilo-trainer/data/model/extern/DCModelV1.4-renault-1614446893.405174")
#data_manager.copy_sample("/home/nigiva/git/lopilo-trainer/data/sample/extern/renault_merged_58800.eslr")
brain = Brain(data_manager)
joystick = JoystickController(0)
data_manager.next()

client = Client("127.0.0.1", 9091, convert_json2img = True)
controller = Controller(client = client, hardware = joystick, data_manager = data_manager, brain = brain)