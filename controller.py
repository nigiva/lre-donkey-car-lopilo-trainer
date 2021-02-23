from threading import Thread

class Controller:
    def __init__(self, client, hardware):
        self.client = client
        self.hardware = hardware

        self.running = True

        self.controller_thread = Thread(target=self.loop)
        self.controller_thread.start()

    
    def loop(self):
        while self.running:
            self.manual_mode()
            if self.hardware.get_exit_app_controller():
                self.client.send_exit_app()
                self.running = False
    
    def manual_mode(self):
        angle = self.hardware.get_angle_controller()
        throttle = self.hardware.get_throttle_controller()
        brake = self.hardware.get_brake_controller()
        self.client.send_car_control(angle, throttle, brake)