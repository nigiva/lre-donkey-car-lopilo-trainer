import os
import shutil
from utils.uid import UID
from tqdm import tqdm
import json
from PIL import Image
import base64
from io import BytesIO
import pandas as pd
import tensorflow as tf
from time import time
from tensor_builder import DonkeyCarTensorBuilder

class DataManager:
    """
    Manage all data : model savefiles, log files and samples records
    """
    def __init__(self, data_path, begin_id = 0, input_label = {'input':['path'], 'speed_accel_gyro':['speed', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']}, output_label = {'angle':['user_angle']}, num_parallel_calls = 3, image_shape = (120, 160, 3)):
        self.uid = UID()
        self.data_path = data_path
        self.id = begin_id

        self.model_path = os.path.join(self.data_path, "model", "model_" + self.uid)
        os.mkdir(self.model_path)
        self.log_path = os.path.join(self.data_path, "log", "log_" + self.uid)
        os.mkdir(self.log_path)
        self.sample_path = os.path.join(self.data_path, "sample", "sample_" + self.uid)
        os.mkdir(self.sample_path)

        self.tensor_builder = DonkeyCarTensorBuilder(input_label = input_label, output_label = output_label, num_parallel_calls = num_parallel_calls, image_shape = image_shape)

        self.sample_base = None
        self.sample_file = None

        self.last_time_save = time()

        self.sample_count = 0
        self.log_file = None

    def copy_model(self, path):
        """
        Copy model path in params into context id dir
        """
        self.set_dir("model")
        shutil.copytree(path, self.get_model_path()) 

    def copy_sample(self, path):
        """
        Copy sample path in params into context id dir
        """
        self.set_dir("sample")
        shutil.copy(path, self.get_sample_path())
        self.load_sample()
    
    def load_extern_sample(self, path, copy = False, image_ext = ".jpeg"):
        """
        Load extern dataset to image and csv file
        Load path + ".eslr" if extracted eslr dataset is not found
        :param path: path without extension to dataset
        :param copy: copy the dataset to the folder of save
        """
        images_path = os.path.join(path, "images")
        csv_path = os.path.join(path, "label.csv")
        if os.path.exists(images_path) and os.path.exists(csv_path):
            print("[INFO] Extern samples is already extracted")
            if copy:
                shutil.copytree(path, self.get_model_path())
                self.sample_base = self.get_sample_path()
            else:
                self.sample_base = path            
        elif os.path.exists(path + ".eslr"):
            os.mkdir(path)
            os.mkdir(images_path)
            csv_file = open(csv_path, "w")
            label_head_is_defined = False
                           
            with open(path + ".eslr", "r") as f:
                for i, line in enumerate(tqdm(f)):
                    data_line = json.loads(line)
                    if (data_line["msg_type"] == "telemetry"):
                        if not label_head_is_defined:
                            # Si le header n'a pas encore initialisé
                            label_head_list = list(data_line.keys())
                            label_head_list.remove("msg_type")
                            label_head_list.remove("image")
                            label_head_list = ['path'] + label_head_list
                            label_head_str = ",".join(label_head_list)
                            # Écrire le header dans le CSV
                            csv_file.write(label_head_str + "\n")
                            label_head_is_defined = True
                        # Définir le path de l'image à enregistrer
                        image_absolute_path = os.path.join(images_path, str(i) + image_ext) #XXX
                        data_line['path'] = image_absolute_path
                        Image.open(BytesIO(base64.b64decode(data_line["image"]))).save(image_absolute_path)
                        # Ajouter toutes les données de la ligne lue dans un le CSV
                        # Mettre 0 comme valeur par défaut si la valeur n'est pas trouvée dans data_line
                        data_list_to_write = [str(data_line.get(k, 0)) for k in label_head_list]
                        csv_file.write(",".join(data_list_to_write) + "\n")
            csv_file.close()
            if copy:
                shutil.copytree(path, self.get_model_path())
                self.sample_base = self.get_sample_path()
            else:
                self.sample_base = path
        else:
            print("[ERROR] Extern samples not found : ", path)
    
    def load_sample(self, image_ext = ".jpeg"):
        """
        Convert eslr file to image and csv file
        """
        if os.path.exists(self.get_sample_path()):
            images_path = os.path.join(self.get_dir("sample"), "images")
            csv_path = os.path.join(self.get_dir("sample"), "label.csv")
            os.mkdir(images_path)
            csv_file = open(csv_path, "w")
            label_head_is_defined = False             
            with open(self.get_sample_path(), "r") as f:
                for i, line in enumerate(tqdm(f)):
                    data_line = json.loads(line)
                    if (data_line["msg_type"] == "telemetry"):
                        if not label_head_is_defined:
                            # Si le header n'a pas encore initialisé
                            label_head_list = list(data_line.keys())
                            label_head_list.remove("msg_type")
                            label_head_list.remove("image")
                            label_head_list = ['path'] + label_head_list
                            label_head_str = ",".join(label_head_list)
                            # Écrire le header dans le CSV
                            csv_file.write(label_head_str + "\n")
                            label_head_is_defined = True
                        # Définir le path de l'image à enregistrer
                        image_absolute_path = os.path.join(images_path, str(i) + image_ext) #XXX
                        data_line['path'] = image_absolute_path
                        Image.open(BytesIO(base64.b64decode(data_line["image"]))).save(image_absolute_path)
                        # Ajouter toutes les données de la ligne lue dans un le CSV
                        # Mettre 0 comme valeur par défaut si la valeur n'est pas trouvée dans data_line
                        data_list_to_write = [str(data_line.get(k, 0)) for k in label_head_list]
                        csv_file.write(",".join(data_list_to_write) + "\n")
            csv_file.close()
    
    def add_to_common_pot(self):
        """
        append all record from label.csv to samples.csv in the root
        """
        csv_path = os.path.join(self.get_dir("sample"), "label.csv")
        if os.path.exists(csv_path):
            is_first_time = not os.path.exists(self.get_common_pot())
            common_pot = open(self.get_common_pot(), "a")
            with open(csv_path, "r") as f:
                for i, line in enumerate(tqdm(f)):
                    if i == 0:
                        if is_first_time:
                            common_pot.write(line)#XXX
                            continue
                    common_pot.write(line)
            common_pot.close()

    def get_common_pot(self):
        """
        Get path of common pot file containing all samples collected during the train
        """
        return os.path.join(self.sample_path, "common_pot.csv")

    def get_log_path(self):
        """
        Get log path
        """
        return os.path.join(self.get_dir("log"), "log.json")

    def get_sample_path(self):
        """
        Get sample path
        """
        return os.path.join(self.get_dir("sample"), "sample.eslr")

    def get_model_path(self):
        """
        Get model path
        """
        return os.path.join(self.get_dir("model"), "model")

    def get_dir(self, data_type):
        """
        Get dir in context id for data_type
        :param data_type: "model", "log", "sample"
        """
        return os.path.join(self.data_path, data_type, data_type + "_" + self.uid, str(self.id))

    def set_dir(self, data_type):
        """
        Check if dir exists ortherwise create dir
        :param data_type: "model", "log", "sample"
        """
        path = self.get_dir(data_type)
        if not os.path.exists(path):
            os.mkdir(path)
    
    def set_log(self, history):

        """
        Create a log file and add history in json file
        :param history: history (dict) given by fit function (keras)
        """     
        df = pd.DataFrame(history.history) 
        with open(self.get_log_path(), 'w') as f:
            df.to_json(f)
    
    def next(self):
        """
        Increment id of Data view, in creating subdir for model, log and sample, and close/open sample_file
        """
        self.id += 1
        os.mkdir(self.get_dir("model"))
        os.mkdir(self.get_dir("log"))
        os.mkdir(self.get_dir("sample"))

        if self.sample_file is not None:
            self.sample_file.close()
            self.sample_count = 0
        self.sample_file = open(os.path.join(self.get_dir("sample"), "sample.eslr"), "w")
    
    def append_sample(self, json, delay = 1/50, debug = False):
        """
        Append record to json file (.eslr)
        :param json: json to add
        :param sleep: delay between two record
        """
        t = time()
        if self.sample_file is not None and t - self.last_time_save > delay:
            self.sample_file.write(json + "\n")
            self.sample_count += 1
            self.last_time_save = t
            if debug:
                print(self.sample_count)

    def close(self):
        if self.sample_file is not None:
            self.sample_file.close()
            self.sample_file = None
            self.sample_count = 0

    def make_dataset(self, nbr_base_sample = 500, nbr_common_pot = 500, nbr_current_sample = 1000, batch_size = 64, test_ratio = 0.1):
        """
        Make dataset in self.id - 1 (file is close) directory

        :param ratio_base_sample: ratio of samples selected randomly in 0 dir
        :param ratio_common_pot: ratio of samples selected randomly in 1, 2, self.id - 2 dir
        :param ratio_current_sample: ratio of samples selected randomly in self.id - 1 dir
        """
        self.load_sample()
        base_sample_path = None

        common_pot_path = self.get_common_pot()

        current_sample_path = os.path.join(self.sample_path, str(self.id), "label.csv")
        if not os.path.exists(common_pot_path):
            common_pot_path = current_sample_path

        base_sample_path = common_pot_path
        if self.sample_base is not None and os.path.exists(os.path.join(self.sample_base, "label.csv")):
            base_sample_path = os.path.join(self.sample_base, "label.csv")

        base_sample_pd = pd.read_csv(base_sample_path)
        common_pot_pd = pd.read_csv(common_pot_path)
        current_sample_pd = pd.read_csv(current_sample_path)

        base_sample_size = base_sample_pd.shape[0]
        common_pot_size = common_pot_pd.shape[0]
        current_sample_size = current_sample_pd.shape[0]

        base_sample_tensor = self.tensor_builder.dataset_to_tensor(base_sample_pd).shuffle(base_sample_size)
        common_pot_tensor = self.tensor_builder.dataset_to_tensor(common_pot_pd).shuffle(common_pot_size)
        current_sample_tensor = self.tensor_builder.dataset_to_tensor(current_sample_pd).shuffle(current_sample_size)

        base_sample_tensor = self.tensor_builder.normalize_dataset(self.tensor_builder.load_image(base_sample_tensor))
        common_pot_tensor = self.tensor_builder.normalize_dataset(self.tensor_builder.load_image(common_pot_tensor))
        current_sample_tensor = self.tensor_builder.normalize_dataset(self.tensor_builder.load_image(current_sample_tensor))

        test_base_sample_tensor = base_sample_tensor.take(int(nbr_base_sample * test_ratio))
        test_common_pot_tensor = common_pot_tensor.take(int(nbr_common_pot * test_ratio))
        test_current_sample_tensor = current_sample_tensor.take(int(nbr_current_sample * test_ratio))

        #train_base_sample_tensor = base_sample_tensor.skip(int(nbr_base_sample * test_ratio)).shuffle(nbr_base_sample)
        #train_common_pot_tensor = common_pot_tensor.skip(int(nbr_common_pot * test_ratio)).shuffle(nbr_common_pot)
        #train_current_sample_tensor = current_sample_tensor.skip(int(nbr_current_sample * test_ratio)).shuffle(nbr_current_sample)


        train_base_sample_tensor = base_sample_tensor.shuffle(nbr_base_sample)
        train_common_pot_tensor = common_pot_tensor.shuffle(nbr_common_pot)
        train_current_sample_tensor = current_sample_tensor.shuffle(nbr_current_sample)
        
        test_dataset = test_base_sample_tensor.concatenate(test_common_pot_tensor).concatenate(test_current_sample_tensor)
        test_dataset = test_dataset.batch(batch_size).prefetch(2)

        train_dataset = train_base_sample_tensor.concatenate(train_common_pot_tensor).concatenate(train_current_sample_tensor)
        train_dataset = train_dataset.batch(batch_size).prefetch(2)
        return train_dataset, test_dataset