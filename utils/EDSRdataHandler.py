# -*- coding: utf-8 -*-
"""EDSRdataHandler.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kgqeIuJqXxZb5CYc2vxeki67q3v0x0cf
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
    files = files.shuffle(buffer_size=self.NUM_IMAGES)
    if partition:
      files = files.batch(partition)
      files = list(files.as_numpy_iterator())
  
    return files

  def getFileInfo(self,GCS_File):
    self.NUM_IMAGES = int(GCS_File[GCS_File.find('N')+1:GCS_File.rfind('_')])
    w = int(GCS_File[GCS_File.find('W')+1:GCS_File.rfind('H')])
    h = int(GCS_File[GCS_File.find('H')+1:GCS_File.find('N')])
    self.NUM_CHANNELS = 1
    self.IMG_SHAPE = (w,h,self.NUM_CHANNELS) 
    

  
  
  @tf.function
  def get_tfrecord(self,GCS_File):
    dataset = tf.data.TFRecordDataset(GCS_File,compression_type='ZLIB', 
                                      num_parallel_reads = tf.data.AUTOTUNE)
    
    return dataset

  @tf.function
  def read_tfrecord(self,example):
    #Write this info into the filename
    
  # Create a dictionary describing the features.
    features = {
      'Mixdown': tf.io.FixedLenFeature([], tf.string),
      'Bass': tf.io.FixedLenFeature([], tf.string),
      'Drums': tf.io.FixedLenFeature([], tf.string),
      'Vocals': tf.io.FixedLenFeature([], tf.string),
      'Other': tf.io.FixedLenFeature([], tf.string)
  }
    
    example = tf.io.parse_example(example, features)

    Mixdown = tf.map_fn(tf.io.decode_png, example['Mixdown'], fn_output_signature=tf.uint8)
    Mixdown = tf.map_fn(lambda Mixdown: tf.reshape(Mixdown, [self.IMG_SHAPE[0],
                                                             self.IMG_SHAPE[1], 
                                                             self.NUM_CHANNELS]), Mixdown)
    
    Mixdown = tf.map_fn(lambda Mixdown: tf.divide(Mixdown,255),
                        Mixdown, 
                        fn_output_signature = tf.float32)


    Bass = tf.map_fn(tf.io.decode_png, example['Bass'], fn_output_signature=tf.uint8)
    Bass = tf.map_fn(lambda Instrument: tf.reshape(Instrument, [self.IMG_SHAPE[0],
                                                                self.IMG_SHAPE[1], 
                                                                self.NUM_CHANNELS]), Bass)
    Bass = tf.map_fn(lambda Instrument: tf.divide(Instrument,255),
                     Bass, 
                     fn_output_signature = tf.float32)
    
    Drums = tf.map_fn(tf.io.decode_png, example['Drums'], fn_output_signature=tf.uint8)
    Drums = tf.map_fn(lambda Instrument: tf.reshape(Instrument, [self.IMG_SHAPE[0],
                                                                 self.IMG_SHAPE[1], 
                                                                 self.NUM_CHANNELS]), Drums)
    Drums = tf.map_fn(lambda Instrument: tf.divide(Instrument,255),
                      Drums, 
                      fn_output_signature = tf.float32)
    
    Vocals = tf.map_fn(tf.io.decode_png, example['Vocals'], fn_output_signature=tf.uint8)
    Vocals = tf.map_fn(lambda Instrument: tf.reshape(Instrument, [self.IMG_SHAPE[0],
                                                                  self.IMG_SHAPE[1], 
                                                                  self.NUM_CHANNELS]), Vocals)
    Vocals = tf.map_fn(lambda Instrument: tf.divide(Instrument,255),
                       Vocals, 
                       fn_output_signature = tf.float32)
    
    Other = tf.map_fn(tf.io.decode_png, example['Other'], fn_output_signature=tf.uint8)
    Other = tf.map_fn(lambda Instrument: tf.reshape(Instrument, [self.IMG_SHAPE[0],
                                                                 self.IMG_SHAPE[1], 
                                                                 self.NUM_CHANNELS]), Other)
    Other = tf.map_fn(lambda Instrument: tf.divide(Instrument,255),
                      Other, 
                      fn_output_signature = tf.float32)
    
    
    
    return Mixdown, Vocals #(Bass, Drums, Vocals, Other)
  
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
    dataset = dataset.repeat()
    dataset = dataset.prefetch(buffer_size=tf.data.AUTOTUNE)
    return dataset

#EXAMPLE
# dh = dataHandler()
# files = dh.listFiles('')
# for partion in files:
#   ds = dh.build_dataset(partition, 32)
#   for (LR,HR,LR_label,HR_label) in ds.take(-1):
#       print('HR Shape: ' + str(np.shape(HR)) + ' LR Shape: ' + str(np.shape(LR)))

# #EXAMPLE
# dh = dataHandler()
# files = dh.listFiles('/content/')
# ds = dh.build_dataset(files, 1)
# for (a,(b,c,d,e)) in ds.take(10):
#   print('{},{},{},{},{}'.format(np.shape(a),
#                                 np.shape(b),
#                                 np.shape(c),
#                                 np.shape(d),
#                                 np.shape(e)))
