"""
Lopilo Trainer
inspired by : Henri `Lopilo` JAMET

Don't forget adapt lines with #XXX (CamConf, Transformer_input, Transformer_output, ...)
"""

import os
import sys

os.environ['DISPLAY'] = ':1'
os.environ['QT_DEBUG_PLUGINS'] = '1'
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

# Car type(donkey | bare | car01), R, G, B, Name, Font size
car_config = ("car01", 255, 85, 0, "Les Copains d'abord", 25)

data_manager = DataManager("/home/nigiva/git/lopilo-trainer/data/")
data_manager.copy_model("/home/nigiva/git/lopilo-trainer/data/model/extern/DCDeepModelV3.2-reda-renault-speed_accel_gyro-80epochs-1617135039.4177356")
#data_manager.load_extern_sample("/home/nigiva/git/lopilo-trainer/data/sample/extern/corentin_renault_20000_record_controller")
brain = Brain(data_manager)
joystick = JoystickController(0)
data_manager.next()


# sim.diyrobocars.fr
client = Client("127.0.0.1", 9091, convert_json2img = True)
client.send_scene("roboracingleague_1")
#cc = CamConf(fov=100, fish_eye_x=0.1, fish_eye_y=0.0, img_w=160, img_h=120, img_d=3,
#                    img_enc="JPEG", offset_x=0.0, offset_y=3.5, offset_z=2.0, rot_x=70.0) #XXX
#client.set_cam_conf(cc)
controller = Controller(client = client, hardware = joystick, data_manager = data_manager, brain = brain, autopilote = True, car_config = car_config)
