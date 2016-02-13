#!/usr/bin/env python
from __future__ import print_function, division
import sys
import numpy as np
import matplotlib.pyplot as plt
import pdb
import os
import astropy.io.fits as pyfits
import glob
import time
import matplotlib.cm as cm

from photutils import irafstarfind
plt.ion()

if len(sys.argv)==1:
    print("Useage: focus_help [dir]")
    sys.exit()
    
dir = sys.argv[1]

old_files = []
while True:
    files = glob.glob(dir + '/*.fit*')
    if len(files) > len(old_files):
        im = pyfits.getdata(files[-1]).astype(np.int)
        im -= np.median(im)
        #pdb.set_trace()
        plt.imshow( np.arcsinh(im/1e2), aspect='auto', interpolation='nearest', cmap=cm.gray)
        plt.draw()
        sources = irafstarfind(im, 600.0,4,roundhi=0.7)
        print("{0:d} sources detected in file {1:s}.".format(len(sources),files[-1]))
        print("Median FWHM = {0:6.2f}".format(np.median(sources["fwhm"])))
        plt.plot(sources["xcentroid"],sources["ycentroid"],'rx')
        plt.axis([0,im.shape[1],im.shape[0],0])
        plt.draw()
        old_files = files
    time.sleep(0.5)
        

