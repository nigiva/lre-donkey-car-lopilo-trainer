from datetime import datetime
from random import randint

def UID():
    now = datetime.now()
    uid = now.strftime("%m-%d-%Y_%H-%M-%S_") + str(randint(1000,9999))
    return uid