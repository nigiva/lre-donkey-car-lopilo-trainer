from threading import Thread
import json
import cv2
import numpy as np
import os
from time import time
os.environ['DISPLAY'] = ':1'

class Controller:
    def __init__(self, client, hardware, data_manager, brain = None, autopilote = True, car_config = None):
        self.client = client
        self.hardware = hardware
        self.brain = brain
        self.data_manager = data_manager

        self.autopilote = autopilote
        self.running = True

        self.is_passed_once = False
        self.last_node = 0
        self.number_turn = -1
        self.time_last_turn = 0
        self.time_ref = None

        self.car_is_driving = False
        self.car_config = car_config

        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()

        self.last_time = None
        self.fps = 0
    
    def loop(self):
        """
            Control loop where the car is driven either in manual mode, either in auto mode
        """
        if self.car_config is not None:
            self.client.send_car_config(*self.car_config)# Car Name
        while self.running:
            ### Stats ###
            # Count number of turn
            # Print Active Node and Cumulative time of last turn
            if self.client.data is not None:
                current_node = self.client.data['activeNode']
                current_time = self.client.data['time']
                if self.last_node > 110 and current_node < 3 and not self.is_passed_once:
                    print(">>>>>> ", self.last_node, current_node, self.is_passed_once)
                    self.number_turn += 1
                    if self.number_turn == 0:
                        self.time_ref = current_time
                    self.last_node = current_node
                    self.is_passed_once = True
                    self.time_last_turn = current_time - self.time_ref
                if current_node > 3:
                    self.is_passed_once = False
                self.last_node = current_node
                print("[INFO]", "turn = ", self.number_turn, "/ activeNode =", current_node, "/ Cumulative time since last turn =", self.time_last_turn)
            ### End of stats ###
            if self.client.img is not None:
                ### FPS
                if self.last_time == None :
                    self.last_time = time()
                else:
                    current_time = time()
                    delta = current_time - self.last_time
                    if delta >= 10:
                        print("---------------------------")
                        print("FPS : ", self.fps/delta)
                        self.last_time = time()
                        self.fps = 0
                    else:
                        self.fps += 1
                ###
                cv2.imshow('view', cv2.cvtColor(np.array(self.client.img), cv2.COLOR_BGR2RGB))
                cv2.waitKey(1)
            if self.hardware.get_autodrive_controller():
                self.manual_mode(record = True)
            elif self.autopilote:
                if self.car_is_driving or self.hardware.get_start_car():
                    self.car_is_driving = True
                    self.auto_mode()
            else:
                self.manual_mode(record = False)
            if self.hardware.get_rec_controller():
                #
                angle = self.hardware.get_angle_controller()
                throttle = self.hardware.get_throttle_controller()
                brake = self.hardware.get_brake_controller()
                self.client.data['user_angle'] = angle
                self.client.data['user_throttle'] = throttle
                self.client.data['user_brake'] = brake
                self.data_manager.append_sample(json.dumps(self.client.data), delay = 1/20, debug = True)
            if self.hardware.get_train_controller():
                if self.data_manager.sample_count != 0:
                    self.data_manager.close()
                    self.client.send_car_control(0, 0, 1)
                    train_dataset, test_dataset = self.data_manager.make_dataset()
                    self.brain.train(train_dataset = train_dataset, test_dataset = test_dataset, nbr_epoch= 5)
                    self.data_manager.add_to_common_pot()
                    self.data_manager.next()
                    self.client.send_reset()
            if self.hardware.get_reset_controller():
                self.car_is_driving = False
                self.client.send_reset()

                # Reset stats
                self.is_passed_once = False
                self.last_node = 0
                self.number_turn = -1
                self.time_last_turn = 0
                self.time_ref = None

            if self.hardware.get_exit_app_controller():
                self.client.stop()
                self.running = False
                exit()
    
    def auto_mode(self):
        """
            Auto mode
            The brain predict and drive the car
        """
        if self.client.img is not None and self.client.data is not None:#
            angle, throttle, brake = self.brain.predict(self.client.img, self.client.data['speed'], self.client.data['accel_x'], self.client.data['accel_y'], self.client.data['accel_z'], self.client.data['gyro_x'], self.client.data['gyro_y'], self.client.data['gyro_z'])
            print(angle, throttle, brake)
            self.client.send_car_control(angle, throttle, brake)

    def manual_mode(self, record = False):
        """
            Manual mode
            The user via his hardware drive the car
        """
        angle = self.hardware.get_angle_controller()
        throttle = self.hardware.get_throttle_controller()
        brake = self.hardware.get_brake_controller()
        self.client.send_car_control(angle, throttle, brake)
        if record and self.brain is not None and self.client.img is not None:
            #
            self.client.data['user_angle'] = angle
            self.client.data['user_throttle'] = throttle
            self.client.data['user_brake'] = brake
            data = json.dumps(self.client.data)
            angle_p, throttle_p, brake_p = self.brain.predict(self.client.img, self.client.data['speed'], self.client.data['accel_x'], self.client.data['accel_y'], self.client.data['accel_z'], self.client.data['gyro_x'], self.client.data['gyro_y'], self.client.data['gyro_z'])#
            if abs(angle - angle_p) > 0.1:
                print(self.data_manager.sample_count)
                self.data_manager.append_sample(data)
