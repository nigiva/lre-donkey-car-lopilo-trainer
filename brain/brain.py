import numpy as np
import tensorflow as tf
from tensorflow import keras

class Brain:
    def __init__(self, model_path, data_manager):
        self.model = None
        self.load(model_path)
        self.data_manager = data_manager
    
    def load(self, model_path):
        """
        Load a model from filepath
        """
        self.model = keras.models.load_model(model_path)

    def predict(self, img):
        """
        Predict actions
        :return (angle, throttle, brake)
        """
        transformed_input = self.input_transformer(img)
        output = self.model.predict({'input' : transformed_input})
        transformed_output = self.output_transformer(output)
        return transformed_output
    
    def train(self, img, nbr_epoch = 4):
        pass
    
    def input_transformer(self, img):
        """
        Transform input before passing in arguments to predict/train function
        :return Tensor
        """
        img = np.array(img)
        img = np.array([img])
        img_tensor = tf.convert_to_tensor(img, dtype=tf.float32)
        img_tensor = tf.image.rgb_to_grayscale(img_tensor)
        img_tensor = (img_tensor/127.5) - 1
        return img_tensor
    
    def output_transformer(self, output):
        """
        Transform output from predict function
        :return (angle, throttle, brake)
        """
        angle = output['angle'][0][0]
        angle_satured = 0.4 if abs(angle) > 0.4 else abs(angle)
        throttle = 0.6 - angle_satured
        return (angle, throttle, 0)
    