# -*- coding: utf-8 -*-
"""files_toDataset.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1pAWQQkM2EjLZbafxW2d6tsxSlNaq4cO3
"""

import tensorflow as tf
# Add functions to convert to a spectrogram

def getPredictFiles(folder_path, extension = '*.wav'):

  files = tf.io.gfile.glob(folder_path + img_format)
  dataset = tf.data.Dataset.from_tensor_slices(files)
  
  if extension == '*.wav':
    dataset = files.map(WAV_to_Dataset)
  
  else:
    dataset = files.map(PNG_to_Dataset)
  
  dataset = dataset.batch(np.shape(files)[0])
  return dataset, files



def PNG_to_Dataset(file):
  image = tf.image.decode_png(tf.io.read_file(file))

  return image

def WAV_to_Dataset(file):
  image = tf.audio.decode_wav(tf.io.read_file(file))

  return image


