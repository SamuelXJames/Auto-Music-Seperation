# -*- coding: utf-8 -*-
"""trainer.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IQclpWe7OSLlQ6r9LEysKU-q4El49pc8
"""

import tensorflow as tf
import numpy as np
import os, datetime
import matplotlib.pyplot as plt 
from PIL import Image
from models import edsr, cunet, edsrtest, medsr
from predict import files_toDataset
from utils.CUNETdataHandler import dataHandler as CUNETdataHandler
from utils.EDSRdataHandler import dataHandler as EDSRdataHandler
from utils.MEDSRdataHandler import dataHandler as MEDSRdataHandler
from utils.testedsrdatahandler import dataHandler as TestdataHandler
from utils import files_toDataset as ftd
from training.progressCallback import CheckProgressCallback
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint, LearningRateScheduler
from tensorflow.python.client import device_lib



class Trainer:


  def __init__(self, 
               model = None, 
               save_path = None,
               train_path = None,
               valid_path = None,
               progress_folder = None,
               progress_save_folder = None,
               progress_freq = 5,
               test_path = None, 
               weights_path = None,
               batch_size = 32,
               epochs = 1000,
               learning_rate_params={'cycle': 9, 
                                     'min': 0.001, 
                                     'max': 0.005,
                                     'start':0.001},
               learning_function = None,
               adam_optimizer={'beta1': 0.9, 
                               'beta2': 0.999, 
                               'epsilon': None},
               loss = 'mae',
               steps_per_execution = 1,
               save_freq = 5,
               cache = False,
               shuffle = False,
               tpu = False,
               train = True):
    
    if tpu:
      resolver = tf.distribute.cluster_resolver.TPUClusterResolver(tpu='')
      tf.config.experimental_connect_to_cluster(resolver)
      tf.tpu.experimental.initialize_tpu_system(resolver)
      print("All devices: ", tf.config.list_logical_devices('TPU'))
      self.strategy = tf.distribute.TPUStrategy(resolver)
    
    else:
      self.strategy = tf.distribute.OneDeviceStrategy(device="/gpu:0")
      print(device_lib.list_local_devices())
    self.TPU = tpu
    self.model_name = model
    self.model = model
    self.train_path = train_path
    self.valid_path = valid_path
    self.test_path = test_path
    self.progress_save_folder = progress_save_folder
    self.weights_path = weights_path

    self.save_freq = save_freq
    self.batch_size = batch_size
    self.epochs = epochs
    self.steps_per_execution = steps_per_execution 
    self.save_path = save_path + '/cp-{epoch:04d}.hdf5'
    self.cache = cache
    self.shuffle = shuffle
    self.adam_optimizer = adam_optimizer
    self.loss = loss
    
    if train:
      self.learning_rate_params = learning_rate_params
      self.dh = self.getdataHandler() # Might want to just have one dataHandler.py
      self.learning_rate = self.lr_function(params = learning_rate_params, 
                                          lr = learning_function)
      if progress_folder:
        self.progress_dataset, self.progress_files = self.getPredData(progress_folder)
    
    else:
      self.getSavedModel(weights_path)

    
    
    

  def getdataHandler(self):
    
    if self.model_name == 'edsr':
      dh = EDSRdataHandler()
      _ = dh.listFiles(self.train_path) # This is just to call dh.listfiles()
    elif self.model_name == 'cunet':
      dh = CUNETdataHandler()
      _ = dh.listFiles(self.train_path) # This is just to call dh.listfiles()
    elif self.model_name == 'test':
      dh = TestdataHandler()
    
    elif self.model_name == 'medsr':
      dh = MEDSRdataHandler()
    
    
    return dh

  # Returns Training, Validation and Testing Datasets (as TF Datasets)  
  def getData(self,train_path,valid_path):
    train_files = self.dh.listFiles(train_path)
    train_data = self.dh.build_dataset(train_files,self.batch_size)
    

    valid_files = self.dh.listFiles(valid_path)
    valid_data = self.dh.build_dataset(valid_files,self.batch_size)
    

    if self.cache:
      train_data = train_data.cache() #Cache if space permits 
      valid_data = valid_data.cache()
     
    
    if self.shuffle:
      train_data = train_data.shuffle()

    return train_data, valid_data


  
  def get_steps_epoch(self,path):
    files = tf.io.gfile.glob(os.path.join(path,'*.tfrec'))
    num_files = np.shape(files)[0] - 1
    m = int(files[0][files[0].find('N')+1:files[0].rfind('_')])
    b = int(files[-1][files[-1].find('N')+1:files[-1].rfind('_')])

    if self.model_name == 'cunet':
      steps_per_epoch = np.ceil((m*num_files+b)/self.batch_size)
      
    

    if self.model_name == 'edsr':
      steps_per_epoch = np.ceil((160*(m*num_files+b))/self.batch_size)
    
    return steps_per_epoch
    
    
  

  # Add all the possible models
  def getModel(self,model):
    if model == 'edsr':
      model = edsr.generator()
    
    elif model == 'cunet':
      model = cunet.cunet_model(shape = self.dh.IMG_SHAPE)
    
    elif model == 'test':
      model = edsrtest.generator()
    
    elif model == 'medsr':
      model = medsr.generator()

    return model

  def getPredData(self,pred_folder):
    predData,files = ftd.getPredictFiles(pred_folder,extension = '*.png')
    return predData,files

  
  
  
  def callbacks(self):
   
    cp = ModelCheckpoint(self.save_path,
                         monitor='val_loss',
                         save_best_only = 'False',
                         period = self.save_freq,
                         verbose = 1)
    
    lr = LearningRateScheduler(self.lr_scheduler,
                               verbose = 1)
    if self.TPU ==False:
      log_dir = os.path.join("logs", datetime.datetime.now().strftime("%m_%d_%Y-%H_%M"))
      tb = TensorBoard(log_dir = log_dir,
                       update_freq='epoch')
      return [tb,cp,lr]
    
    else:
      return [cp,lr]
    

  # CRT Learning Rate
  def lr_function(self,params=None,lr = None):
    if lr:
      return lr
    else:
      cycle = params['cycle']
      y_min = params['min']
      y_max = params['max']
      x_0 = params['start']

      sign = 1
      x = np.arange(self.epochs)+1
      lr = np.empty(self.epochs)
      lr[0] = x_0
      slope = y_max/((cycle-1)/2);
      for i in x[0:-1]:
        if sign == 1:
          lr[i] = np.min([lr[i-1]+sign*slope,y_max])
      
        if sign == -1:
          lr[i] = np.max([lr[i-1]+sign*slope,y_min])
      
        if lr[i] == y_max:
          sign = -1
      
        elif lr[i] == y_min:
          sign = 1
          y_max = np.max([y_max*0.5,y_min])
          slope = slope/2
      return lr

  def lr_scheduler(self,epoch,lr):
    lr = self.learning_rate[epoch]
    return lr

  # plots the learning rate as a function of epochs
  def plot_lr_schedule(self):
        
    plt.plot(np.arange(np.shape(self.learning_rate)[0])+1,self.learning_rate)
    plt.xlabel('Epochs')
    plt.ylabel('Learning Rate')
    plt.title('Learning Rate Scheduler')    

    return None

  def get_initial_epoch(self):
    files = self.weights_path
    if self.weights_path:
      initial_epoch = int(files[files.rfind('-')+1:files.rfind('.')])
    else:
      initial_epoch = 0
    return initial_epoch

  def train(self):
    with self.strategy.scope():
      self.model = self.getModel(self.model)
      
      if self.weights_path:
        self.model.load_weights(self.weights_path)
      else:
        print('No Pre-Trained Weights Selected: Training will Start at Epoch 1')


      
      train_data, valid_data = self.getData(self.train_path,
                                            self.valid_path)
                                          
      callbacks = self.callbacks()
      optimizer = Adam(learning_rate = self.learning_rate_params['start'],
                       beta_1 = self.adam_optimizer['beta1'],
                       beta_2 = self.adam_optimizer['beta2'],
                       epsilon = self.adam_optimizer['epsilon'])

      self.model.compile(optimizer = optimizer,
                         steps_per_execution = self.steps_per_execution,
                         loss = self.loss,
                         metrics=[tf.keras.metrics.MeanAbsoluteError()])
                          
    
    self.model.fit(train_data,
                   epochs = self.epochs,
                   validation_data = valid_data,
                   validation_steps = self.get_steps_epoch(self.valid_path),
                   callbacks = callbacks,
                   steps_per_epoch = self.get_steps_epoch(self.train_path),
                   initial_epoch = self.get_initial_epoch())
    
                   
    def test_model(self):
      test_files = self.dh.listFiles(self.test_path)
      test_data = self.dh.build_dataset(test_files,self.batch_size)
      test_data = test_data.cache()

      self.model.evaluate(test_data)
    
    def getSavedModel(self,
                      weights_path)
    
    self.model = getModel(self.model_name)
    self.model.load_weights(weights_path)
    

      return None