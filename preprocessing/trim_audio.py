#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 18:56:12 2021

@author: albert
"""

from pydub import AudioSegment                                         
import numpy as np
import math


def myRange(start,end,step):
    i = start
    while i < end:
        yield i
        i += step
    yield end
    
def trim_audio(filename):
    
    mixture = {}
    sample = {}
    sample_np ={}
    song = AudioSegment.from_wav(filename)
    song = song.set_channels(1)
    five_seconds = 5* 1000;
    count = 0
    start = 0
    for i in myRange(5000, len(song),5000):
        mixture['%d' % count] = song[start:i]
        sample['%d' % count] = mixture[str(count)].get_array_of_samples()
        sample['%d' % count] = np.float32(sample['%d' % count])
        sample_np['%d' % count] = np.array(sample[str(count)])
        start = i
        count +=1
   # sample_np = np.float32(sample_np)
    num_zeros = len(sample_np["0"]) - len(sample_np[str(count-1)])
    #np.zeros(num_zeros)
    sample_np[str(count-1)] = np.hstack((sample_np[str(count-1)], np.zeros(num_zeros)))
    return sample_np
if __name__ == '__main__':
    data = trim_audio("mixture.wav")
    
    
