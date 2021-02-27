"""
Lopilo Trainer
inspired by : Henri `Lopilo` JAMET

Don't forget adapt lines with #XXX (CamConf, Transformer_input, Transformer_output, ...)
"""

import os
import sys

# For avoid warning in Visual Code
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from core.client import Client
from core.camconf import CamConf
from hardware.joystick import JoystickController
from controller import Controller
from brain.brain import Brain
from manager import DataManager

data_manager = DataManager("/home/nigiva/git/lopilo-trainer/data/")
data_manager.copy_model("/home/nigiva/git/lopilo-trainer/data/model/extern/DCDeepModelV2-renault-1614457001.1865957")
data_manager.copy_sample("/home/nigiva/git/lopilo-trainer/data/sample/extern/alexis_renault_cam_rot_43000.eslr")
brain = Brain(data_manager)
joystick = JoystickController(0)
data_manager.next()

client = Client("127.0.0.1", 9091, convert_json2img = True)
cc = CamConf(fov=100, fish_eye_x=0.1, fish_eye_y=0.0, img_w=160, img_h=120, img_d=3,
                    img_enc="PNG", offset_x=0.0, offset_y=3.5, offset_z=2.0, rot_x=70.0) #XXX
client.set_cam_conf(cc)
controller = Controller(client = client, hardware = joystick, data_manager = data_manager, brain = brain)