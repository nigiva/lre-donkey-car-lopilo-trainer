import os
import sys
from core.client import Client

# For avoid warning in Visual Code
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)


Client("127.0.0.1", 9091, convert_json2img = True)