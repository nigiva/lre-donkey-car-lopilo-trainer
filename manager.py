import os
import shutil
from utils.uid import UID

class DataManager:
    """
    Manage all data : model savefiles, log files and samples records
    """
    def __init__(self, data_path, begin_id = 0):
        self.uid = UID()
        self.data_path = data_path
        self.id = begin_id

        self.model_path = os.path.join(self.data_path, "model", "model_" + self.uid)
        os.mkdir(self.model_path)
        self.log_path = os.path.join(self.data_path, "log", "log_" + self.uid)
        os.mkdir(self.log_path)
        self.sample_path = os.path.join(self.data_path, "sample", "sample_" + self.uid)
        os.mkdir(self.sample_path)

        self.sample_file = None
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
        return os.path.join(self.data_path, data_type, + data_type + "_" + self.uid, self.id)

    def set_dir(self, data_type):
        """
        check if dir exists ortherwise create dir
        :param data_type: "model", "log", "sample"
        """
        path = self.get_dir(data_type)
        if not os.path.exists(path):
            os.mkdir(path)
    
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
        self.sample_file = open(os.path.join(self.get_dir("sample"), "sample.eslr"), "w")
    
    def close(self):
        if self.sample_file is not None:
            self.sample_file.close()
            self.sample_file = None
    
    def make_dataset(self, ratio_base_id = 0.30, ratio_other_id = 0.40, ratio_current_id = 0.30):
        """
        Make dataset in self.id - 1 (file is close) directory

        :param ratio_base_id: ratio of samples selected randomly in 0 dir
        :param ratio_other_id: ratio of samples selected randomly in 1, 2, self.id - 2 dir
        :param ratio_current_id: ratio of samples selected randomly in self.id - 1 dir
        """
        pass

    def get_dataset_path(self):
        """
        Return preprocessed dataset path 
        """
        pass
    


    