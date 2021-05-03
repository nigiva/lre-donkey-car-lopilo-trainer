import tensorflow as tf

class DonkeyCarTensorBuilder:
  def __init__(self, input_label = {'input':['path']}, output_label = {'angle':['user_angle']}, num_parallel_calls = 3, image_shape = (120, 160, 3)):
    self.input_label = input_label
    self.output_label = output_label
    
    self.num_parallel_calls = num_parallel_calls
    self.image_shape = image_shape
  
  @staticmethod
  def normalize(img):
    return (img / 127.5) - 1.0
  
  @staticmethod
  def unnormalize(img):
    return (img + 1.0) * 127.5

  def dataset_to_tensor(self, dataset):
    """
    {"input" : dataset['path'], "speed_accel_gyro" : dataset[['speed', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']]}, {"angle" : dataset['angle']}
    :return: Tensor
    """
    input_dict = {}
    output_dict = {}

    # Inputs
    for k, l in self.input_label.items():
      if len(l) != 0:
        if len(l) == 1:
          input_dict[k] = dataset[l[0]]
        else:
          input_dict[k] = dataset[l]

    # Outputs
    for k, l in self.output_label.items():
      if len(l) != 0:
        if len(l) == 1:
          output_dict[k] = dataset[l[0]]
        else:
          output_dict[k] = dataset[l]
    return tf.data.Dataset.from_tensor_slices((input_dict, output_dict))
  
  def load_image(self, dataset_tensor):
    def load_image_map_func(inputs, outputs):
      loaded_inputs = dict(inputs)

      img = tf.io.read_file(inputs['input'])
      img = tf.cast(tf.image.decode_jpeg(img, channels=3), dtype=tf.float32)
      img = tf.reshape(img, self.image_shape)
      loaded_inputs['input'] = img

      return loaded_inputs, outputs
    return dataset_tensor.map(load_image_map_func, num_parallel_calls = self.num_parallel_calls)
  
  def normalize_dataset(self, dataset_tensor):
    def normalize_map_func(inputs, outputs):
      transformed_inputs = dict(inputs)
      transformed_img = inputs['input']
      transformed_img = DonkeyCarTensorBuilder.normalize(transformed_img)
      transformed_img = tf.reshape(transformed_img, self.image_shape)
      transformed_inputs['input'] = transformed_img
      return transformed_inputs, outputs
    return dataset_tensor.map(normalize_map_func, num_parallel_calls = self.num_parallel_calls)