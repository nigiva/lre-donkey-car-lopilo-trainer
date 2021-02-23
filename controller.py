from threading import Thread

class Controller:
    def __init__(self, client, hardware, brain = None):
        self.client = client
        self.hardware = hardware
        self.brain = brain

        self.running = True

        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()

    
    def loop(self):
        while self.running:
            if self.hardware.get_autodrive_controller():
                self.manual_mode()
            else:
                self.auto_model()
            if self.hardware.get_reset_controller():
                self.client.send_reset()
            if self.hardware.get_exit_app_controller():
                self.client.stop()
                self.running = False
                exit()
    
    def auto_model(self):
        if self.client.img is not None:
            angle, throttle, brake = self.brain.predict(self.client.img)
            print(angle, throttle, brake)
            self.client.send_car_control(angle, throttle, brake)

    def manual_mode(self):
        angle = self.hardware.get_angle_controller()
        throttle = self.hardware.get_throttle_controller()
        brake = self.hardware.get_brake_controller()
        self.client.send_car_control(angle, throttle, brake)