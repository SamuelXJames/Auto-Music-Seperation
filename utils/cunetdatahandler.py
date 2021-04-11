# -*- coding: utf-8 -*-
"""CUNETdataHandler.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KbpDRQQxhSXCirDj2fw6eA9JrYx1xSYO
"""

import numpy as np
import os, sys, math, glob, ntpath,time
import tensorflow as tf
import timeit

class dataHandler:

  def __init__(self):
    
    
    return None
  
  
  def listFiles(self,tfr_dir,partition = None):
    files = tf.data.Dataset.list_files(os.path.join(tfr_dir,'*.tfrec'))
    
    sample_file = tf.io.gfile.glob(os.path.join(tfr_dir,'*.tfrec'))[0]
    self.getFileInfo(sample_file)
    if partition:
      files = files.batch(partition)
      files = list(files.as_numpy_iterator())
  
    return files

  def getFileInfo(self,GCS_File):
    self.NUM_IMAGES = int(GCS_File[GCS_File.find('N')+1:GCS_File.rfind('_')])
    w = int(GCS_File[GCS_File.find('W')+1:GCS_File.rfind('H')])
    h = int(GCS_File[GCS_File.find('H')+1:GCS_File.rfind('N')])
    self.IMG_SHAPE = [w,h] 
    self.NUM_CHANNELS = 1

  
  
  @tf.function
  def get_tfrecord(self,GCS_File):
    dataset = tf.data.TFRecordDataset(GCS_File,compression_type='ZLIB', 
                                      num_parallel_reads = tf.data.AUTOTUNE)
    
    return dataset

  def scaleData(self,Mixdown,Labels,Instrument):
    Mixdown = dataset[0]
    Labels = dataset[1]
    Instrument = dataset[2]

    Mixdown = tf.math.divide(Mixdown,255)
    Instrument = tf.math.divide(Instrument,255)

    if random.sample(range(0, 4), 1)[0] == 0:
      p = random.uniform(0, 1)
      Instrument = tf.math.multiply(Instrument, p)
      Label = tf.math.multiply(Label, p) 
      
    return Mixdown,Labels,Instrument
  @tf.function
  def read_tfrecord(self,example):
    #Write this info into the filename
    
  # Create a dictionary describing the features.
    features = {
      'Mixdown': tf.io.FixedLenFeature([], tf.string),
      'Label': tf.io.VarLenFeature(tf.float32),
      'Instrument': tf.io.FixedLenFeature([], tf.string)
      
  }
    
    example = tf.io.parse_example(example, features)

    Mixdown = tf.map_fn(tf.io.decode_png, example['Mixdown'], fn_output_signature=tf.uint8)
    Mixdown = tf.map_fn(lambda Mixdown: tf.reshape(Mixdown, [self.IMG_SHAPE[0],
                                                             self.IMG_SHAPE[1], 
                                                             self.NUM_CHANNELS]), Mixdown)
    #Mixdown = tf.map_fn(lambda Mixdown: tf.cast(Mixdown, tf.float64), Mixdown, fn_output_signature=tf.float64)
    Mixdown = tf.map_fn(lambda Mixdown: tf.divide(Mixdown,255),
                        Mixdown, 
                        fn_output_signature = tf.float32)
    
    Label = tf.map_fn(tf.sparse.to_dense, example['Label'], fn_output_signature = tf.float32)
    Label = tf.map_fn(lambda Label: tf.reshape(Label,[4,1]), Label)


    Instrument = tf.map_fn(tf.io.decode_png, example['Instrument'], fn_output_signature=tf.uint8)
    Instrument = tf.map_fn(lambda Instrument: tf.reshape(Instrument, [self.IMG_SHAPE[0],
                                                                      self.IMG_SHAPE[1], 
                                                                      self.NUM_CHANNELS]), Instrument)
    Instrument = tf.map_fn(lambda Instrument: tf.divide(Instrument,255),
                           Instrument, 
                           fn_output_signature = tf.float32)
    
    if tf.random.shuffle([0,1,2,3])[0] == 0:
      p = tf.random.uniform([1])[0] 
      Label = tf.map_fn(lambda Label: tf.math.multiply(Label,p),
                        Label)
      Instrument = tf.map_fn(lambda Instrument: tf.math.multiply(Instrument,p),
                             Instrument)   

    
    
    return Mixdown, Label, Instrument
  
  #@tf.function
  def build_dataset(self,dataset, batch_size):
    ignore_order = tf.data.Options()
    ignore_order.experimental_deterministic = False

    #If the input is an array of file names, convert it to a dataset
    if type(dataset) == np.ndarray:
      dataset = tf.data.Dataset.from_tensor_slices(dataset)  
    

    dataset = dataset.interleave(self.get_tfrecord,
                                 block_length = 1,
                                 cycle_length = tf.data.AUTOTUNE,
                                 num_parallel_calls = tf.data.AUTOTUNE)
    
    dataset = dataset.batch(batch_size, drop_remainder = False)
  
    dataset = dataset.map(self.read_tfrecord,num_parallel_calls = tf.data.AUTOTUNE)
    #dataset = dataset.map(self.scaleData)
    dataset = dataset.prefetch(buffer_size=tf.data.AUTOTUNE)
    return dataset

#EXAMPLE
# dh = dataHandler()
# files = dh.listFiles('')
# for partion in files:
#   ds = dh.build_dataset(partition, 32)
#   for (LR,HR,LR_label,HR_label) in ds.take(-1):
#       print('HR Shape: ' + str(np.shape(HR)) + ' LR Shape: ' + str(np.shape(LR)))