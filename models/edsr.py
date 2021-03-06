# -*- coding: utf-8 -*-
"""EDSR.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fryqdPvLZtlRL5sufUk6l_hWu-5eE_5_
"""

import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, Activation, Add, Lambda
from tensorflow.keras.models import Model


def res_block(input_tensor, filters, scale=0.1):
    x = Conv2D(filters=filters, kernel_size=3, strides=1, padding='same')(input_tensor)
    x = Activation('relu')(x)

    x = Conv2D(filters=filters, kernel_size=3, strides=1, padding='same')(x)
    if scale:
        x = Lambda(lambda t: t * scale)(x)
    x = Add()([x, input_tensor])

    return x


def sub_pixel_conv2d(scale=2, **kwargs):
    return Lambda(lambda x: tf.nn.depth_to_space(x, scale), **kwargs)


def upsample(input_tensor, filters):
    x = Conv2D(filters=filters * 2, kernel_size=3, strides=1, padding='same')(input_tensor)
    x = sub_pixel_conv2d(scale=2)(x)
    x = Activation('relu')(x)
    return x


def generator_block(inputs,filters=128, n_id_block=16, n_sub_block=1):
    #inputs = Input(shape=(84, 84, 1))

    x = x_1 = Conv2D(filters=filters, kernel_size=3, strides=1, padding='same')(inputs)

    for _ in range(n_id_block):
        x = res_block(x, filters=filters)

    x = Conv2D(filters=filters, kernel_size=3, strides=1, padding='same')(x)

    x = Add()([x_1, x])
    #x = Conv2D(filters = filters, kernel_size = 3, strides=2, padding ='same')(x)
    #for _ in range(n_sub_block):
        #x = upsample(x, filters)
    x = Conv2D(filters=1, kernel_size=3, strides=1, padding='same')(x)
    
    return x
def generator(shape = (None,None,1)):
  inputs = Input(shape)
  #bass = generator_block(inputs)
  #drums = generator_block(inputs)
  vocals = generator_block(inputs)
  #other = generator_block(inputs)
  
  model = Model(inputs=inputs, outputs= vocals)
  return model
