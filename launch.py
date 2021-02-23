import os
import sys

# For avoid warning in Visual Code
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from core.client import Client
from hardware.joystick import JoystickController
from controller import Controller

joystick = JoystickController(0)
client = Client("127.0.0.1", 9091, convert_json2img = True)
controller = Controller(client, joystick)