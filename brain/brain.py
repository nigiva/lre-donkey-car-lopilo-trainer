import numpy as np
import tensorflow as tf
from tensorflow import keras
import os
from .saver import ModelSaver
import shutil

class Brain:
    def __init__(self, data_manager):
        self.model = None
        self.load(data_manager.get_model_path())
        self.data_manager = data_manager
        self.model_path = None
    
    def load(self, model_path, lr = 0.001):
        """
        Load a model from model_path
        :param model_path: directory path
        """
        # self.model = keras.models.load_model(model_path)
        self.model_path = model_path
        DCModel = ModelSaver.load(os.path.join(model_path, "model.code"))
        self.model = DCModel()
        self.model.load_weights(os.path.join(model_path, "weights.data"))
        optimizer = keras.optimizers.Adam(learning_rate=lr)
        self.model.compile(optimizer=optimizer,loss=keras.losses.MSE, metrics=["mse"])

    def save(self):
        """
        Save the brain like a SaveModel, weights.data and model.code
        :param path: directory path where we want save (directory already created)
        """
        if self.model_path is not None:
            shutil.copy(os.path.join(model_path, "model.code"), os.path.join(self.data_manager.get_model_path(), "model.code"))
        #self.model.save(self.data_manager.get_model_path())
        self.model.save_weights(os.path.join(self.data_manager.get_model_path(), "weights.data"))

    def predict(self, img):
        """
        Predict actions
        :return (angle, throttle, brake)
        """
        transformed_input = self.input_transformer(img)
        output = self.model.predict({'input' : transformed_input}) #XXX
        transformed_output = self.output_transformer(output)
        return transformed_output
    
    def train(self, train_dataset, test_dataset, nbr_epoch = 4):
        """
        Train model
        :params train_dataset:
        :params params: 
        :params nbr_epoch: number of epochs
        """
        history = self.model.fit(train_dataset, validation_data=test_dataset, epochs=nbr_epoch, verbose = 1)
        self.data_manager.set_log(history)
        self.save()
    
    def input_transformer(self, img):
        """
        Transform input before passing in arguments to predict/train function
        :return Tensor
        """
        img = np.array(img)
        img = np.array([img])
        img_tensor = tf.convert_to_tensor(img, dtype=tf.float32)
        #img_tensor = tf.image.rgb_to_grayscale(img_tensor) #XXX
        img_tensor = (img_tensor/127.5) - 1
        return img_tensor
    
    def output_transformer(self, output):
        """
        Transform output from predict function
        :return (angle, throttle, brake)
        """
        angle = output['angle'][0][0] #XXX
        angle_satured = 0.4 if abs(angle) > 0.4 else abs(angle)
        throttle = 0.6 - angle_satured
        return (angle, throttle, 0)
    