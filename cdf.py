# Plotting cdf of the throughput
import numpy as np
import matplotlib.pyplot as plt
import sys
import glob
import time, sys, os, random, string, subprocess, urllib2, json, urllib, numpy




def cdf(data, name, provider):

    data_size=len(data)
    # data = [1,5,23,4,6,7,8,4,2,1]

    # Set bins edges
    data_set=sorted(set(data))
    bins=np.append(data_set, data_set[-1]+1)

    # Use the histogram function to bin the data
    counts, bin_edges = np.histogram(data, bins=bins, density=False)
    # (array([2, 1, 2, 1, 1, 1, 1, 1]), array([ 1,  2,  4,  5,  6,  7,  8, 23, 24]))

    counts=counts.astype(float)/data_size
    # array([ 0.2,  0.1,  0.2,  0.1,  0.1,  0.1,  0.1,  0.1]) Probability of each item

    # Find the cdf
    cdf = np.cumsum(counts)
    print cdf
    print name, provider
    temp = np.array(data)

    # Plot the cdf
    plt.plot(bin_edges[0:-1], cdf,label=str(provider)+'_average: '+str(np.round(temp.mean(),2))+'Kbps')

    # Plot the cdf
    plt.ylim((0,1))
    plt.ylabel("CDF")
    plt.xlabel("Download Speed (Kbps)")
    plt.title("CDF of Download Speed (Throughput) of "+ str(name))
    plt.grid(True)
    plt.legend()
    return plt
    # plt.show()


currdir = os.getcwd()
name = ''
provider = ''
plots = []
files = glob.glob(currdir+'/download_netflix/*.txt')
# files = glob.glob(currdir+'/download_netflix/download_netflix_ATTtest.txt')
for file in files:
    print file
    if 'vpn' not in file:  
        continue
    # if 'WiFi' in file:
        # continue
    name = file.split('_')[-2]
    provider = file.split('_')[-1].replace('.txt','')

    f = open(file,'r')
    lines = f.readlines()
    data = []
    for line in lines:
        data.append(float(line.split(',')[1].replace('\n','')))
    cdf(data, name, provider)
# print plots
plt.show() 
# for a in plots:
    # a.show() 




# name  = sys.argv[1]
# provider = sys.argv[2]

# cdf(data, name, provider)
