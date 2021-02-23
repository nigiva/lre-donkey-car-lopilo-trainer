"""
Client

A base class for interacting with the sdsim simulator as server.
The server will create on vehicle per client connection. The client
will then interact by createing json message to send to the server.
The server will reply with telemetry and other status messages in an
asynchronous manner.

Author: Tawn Kramer
Adapted by: Corentin Duchêne
"""
import os
import sys
import time
import socket
import select
from threading import Thread
import json
import logging
from datetime import datetime
import json
from PIL import Image
import base64
from io import BytesIO
import copy
import re

from .camconf import CamConf

def replace_float_notation(string):
    """
    Replace unity float notation for languages like
    French or German that use comma instead of dot.
    This convert the json sent by Unity to a valid one.
    Ex: "test": 1,2, "key": 2 -> "test": 1.2, "key": 2

    :param string: (str) The incorrect json string
    :return: (str) Valid JSON string
    """
    regex_french_notation = r'"[a-zA-Z_]+":(?P<num>[0-9,E-]+),'
    regex_end = r'"[a-zA-Z_]+":(?P<num>[0-9,E-]+)}'

    for regex in [regex_french_notation, regex_end]:
        matches = re.finditer(regex, string, re.MULTILINE)

        for match in matches:
            num = match.group('num').replace(',', '.')
            string = string.replace(match.group('num'), num)
    return string

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, host, port, poll_socket_sleep_time = 0.05, convert_json2img = False):
        self.msg = None
        self.host = host
        self.port = port
        self.poll_socket_sleep_sec = poll_socket_sleep_time
        self.th = None

        self.current_cam_conf = None

        self.data = None
        self.convert_json2img = convert_json2img
        self.img = None

        # the aborted flag will be set when we have detected a problem with the socket
        # that we can't recover from.
        self.aborted = False
        self.connect()


    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connecting to the server 
        logger.info("connecting to %s:%d " % (self.host, self.port))
        try:
            self.s.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            raise(Exception("Could not connect to server. Is it running? If you specified 'remote', then you must start it manually. : " + str(e)))

        # time.sleep(pause_on_create)
        self.do_process_msgs = True
        self.th = Thread(target=self.proc_msg, args=(self.s,))
        self.th.start()

    def get_img(self):
        """
        Get deep copy of the current image captured by the camera
        """
        return copy.deepcopy(self.img)

    def set_cam_conf(self, cam_conf):
        """
        Set the camera configuration and send it

        :param cam_conf: CamConf object
        """
        self.current_cam_conf = cam_conf
        self.send_now(self.cam_conf.conf_json)

    def flush_msg(self, writable):
        """
        Flush buffer and send all to the server
        """
        for s in writable:
            if self.msg != None:
                logger.debug("sending " + self.msg)
                s.sendall(self.msg.encode("utf-8"))
                self.msg = None

    def send_car_config(self, body_style, body_r, body_g, body_b, car_name, font_size):
        """
        Send car config (visual details)

        body_style : donkey | bare | car01
        body_r : string value of integer between 0-255
        body_g : string value of integer between 0-255
        body_b : string value of integer between 0-255
        car_name : string value car name to display over car. Newline accepted for multi-line.
        font_size : string value of integer between 10-100 to set size of car name text
        """
        d = dict()
        d["msg_type"] = "car_config"
        d["body_style"] = str(body_style)
        d["body_r"] = str(body_r)
        d["body_g"] = str(body_g)
        d["body_b"] = str(body_b)
        d["car_name"] = str(car_name)
        d["font_size"] = str(font_size)
        self.send_now(json.dumps(d))

    def send_car_control(self, angle, throttle, brake):
        """
        Send car control (angle ou steering, throttle, brake)
        """
        d = dict()
        d["msg_type"] = "control"
        d["steering"] = str(angle)
        d["throttle"] = str(throttle)
        d["brake"] = str(brake)
        self.send_now(json.dumps(d))

    def send_exit_scene(self):
        """
        Send exit requet to the server
        """
        d = dict()
        d["msg_type"] = "exit_scene"
        self.send_now(json.dumps(d))

    def send_exit_app(self):
        """
        Send exit requet to the server
        """
        d = dict()
        d["msg_type"] = "quit_app"
        self.send_now(json.dumps(d))

    def send_reset(self):
        """
        Send reset the position of car in a requet to the server
        """
        d = dict()
        d["msg_type"] = "reset_car"
        self.send_now(json.dumps(d))

    def send(self, m):
        """
        Add message to send  (without sending)
        """
        self.msg = m

    def send_now(self, msg):
        """
        Send all buffer message
        """
        logger.debug("send_now:" + msg)
        self.s.sendall(msg.encode("utf-8"))

    def on_msg_recv(self, j):
        logger.debug("got:" + j['msg_type'])

    def stop(self):
        # signal proc_msg loop to stop, then wait for thread to finish
        # close socket
        self.do_process_msgs = False
        if self.th is not None:
            self.th.join()
        if self.s is not None:
            self.s.close()


    def proc_msg(self, sock):
        '''
        This is the thread message loop to process messages.
        We will send any message that is queued via the self.msg variable
        when our socket is in a writable state. 
        And we will read any messages when it's in a readable state and then
        call self.on_msg_recv with the json object message.
        '''
        sock.setblocking(0)
        inputs = [ sock ]
        outputs = [ sock ]
        localbuffer=""

        while self.do_process_msgs:
            # without this sleep, I was getting very consistent socket errors
            # on Windows. Perhaps we don't need this sleep on other platforms.
            #time.sleep(0.1)
            time.sleep(self.poll_socket_sleep_sec)
            try:
                # test our socket for readable, writable states.
                readable, writable, exceptional = select.select(inputs, outputs, inputs)

                for s in readable:
                    try:
                        data = s.recv(1024 * 256)
                    except ConnectionAbortedError:
                        logger.warn("socket connection aborted")
                        print("socket connection aborted")
                        self.do_process_msgs = False
                        break

                    # we don't technically need to convert from bytes to string
                    # for json.loads, but we do need a string in order to do
                    # the split by \n newline char. This seperates each json msg.
                    data = data.decode("utf-8")

                    localbuffer += data

                    n0=localbuffer.find("{")
                    n1=localbuffer.rfind("}")
                    if  n1>=0 and n0>=0 and n0<n1 :  # there is at least one message :
                        msgs=localbuffer[n0:n1+1].split("\n")
                        localbuffer=localbuffer[n1:]
                        j = None
                        for m in msgs:
                              if len(m) <= 2:
                                  continue
                              # Replace comma with dots for floats
                              # useful when using unity in a language different from English
                              m = replace_float_notation(m)
                              try:

                                    j = json.loads(m)
                              except Exception as e:
                                    logger.error("Exception:" + str(e))
                                    logger.error("json: " + m)
                                    continue

                              if 'msg_type' not in j:
                                    logger.error('Warning expected msg_type field')
                                    logger.error("json: " + m)
                                    continue
                              else : 
                                    self.on_msg_recv(j)
                        if j is not None and self.convert_json2img and j['msg_type'] == "telemetry":
                            self.img = Image.open(BytesIO(base64.b64decode(j['image'])))
                            self.data = j
                self.flush_msg(writable)
                if len(exceptional) > 0:
                    logger.error("problems w sockets!")

            except Exception as e:
                print("Exception:", e)
                self.aborted = True
                self.on_msg_recv({"msg_type" : "aborted"})
                break