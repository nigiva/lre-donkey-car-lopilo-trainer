import json

class CamConf:
    """
    Class use to store camera configuration
    
    @conf_json : variable convert all config to json request
    """
    def __init__(self, fov=100, fish_eye_x=0, fish_eye_y=0, img_w=160, img_h=120, img_d=3, img_enc="PNG", offset_x=0.0, offset_y=3.5, offset_z=0.0, rot_x=90.0):
        self.conf = dict()
        self.conf["msg_type"] = "cam_config"
        self.conf["fov"] = str(fov)
        self.conf["fish_eye_x"] = str(fish_eye_x)
        self.conf["fish_eye_y"] = str(fish_eye_y)
        self.conf["img_w"] = str(img_w)
        self.conf["img_h"] = str(img_h)
        self.conf["img_d"] = str(img_d)
        self.conf["img_enc"] = str(img_enc)
        self.conf["offset_x"] = str(offset_x)
        self.conf["offset_y"] = str(offset_y)
        self.conf["offset_z"] = str(offset_z)
        self.conf["rot_x"] = str(rot_x)
        self.conf_json = json.dumps(self.conf)