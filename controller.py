from threading import Thread
import json

class Controller:
    def __init__(self, client, hardware, data_manager, brain = None):
        self.client = client
        self.hardware = hardware
        self.brain = brain
        self.data_manager = data_manager

        self.running = True

        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()
    
    def loop(self):
        """
            Control loop where the car is driven either in manual mode, either in auto mode
        """
        while self.running:
            if self.hardware.get_autodrive_controller():
                self.manual_mode(record = True)
            else:
                self.auto_mode()
            if self.hardware.get_rec_controller():
                self.data_manager.append_sample(json.dumps(self.client.data))
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
                self.client.send_reset()
            if self.hardware.get_exit_app_controller():
                self.client.stop()
                self.running = False
                exit()
    
    def auto_mode(self):
        """
            Auto mode
            The brain predict and drive the car
        """
        if self.client.img is not None:
            angle, throttle, brake = self.brain.predict(self.client.img)
            #print(angle, throttle, brake)
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
            data = json.dumps(self.client.data)
            angle_p, throttle_p, brake_p = self.brain.predict(self.client.img)
            if abs(angle - angle_p) > 0.1:
                print(self.data_manager.sample_count)
                self.data_manager.append_sample(data)
