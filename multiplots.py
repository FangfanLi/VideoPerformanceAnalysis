# Plots the video quality of a single video streaming service along with different providers
import glob
import time, sys, os, random, string, subprocess, urllib2, json, urllib, numpy
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
import matplotlib.pyplot as plt
import re
import pickle

def drawQualityChangeGraph(fig, ax, bevents, endtime, filename, contentprovider):
    # fig, ax = plt.subplots()
    plt.ylim((0, 7.5))

    plt.xlim((0, endtime))

    if contentprovider == 'youtube':
        quality2y = {'tiny': 1, 'small': 2, 'medium': 3, 'large': 4, 'hd720': 5, 'hd1080': 6, 'hd1440': 7}
    if contentprovider == 'vimeo':
        quality2y = {'270p': 1, '360p': 2, '540p': 3, '720p': 4, '1080p': 5, '2K': 6, '4K': 7}
    if contentprovider == 'netflix':
        quality2y = {'100': 1, '180': 2, '240': 3, '288':4, '384': 5, '480': 6, '720': 7, '1080': 8, '1400': 9, '2050': 10}
    # The data always starts with buffering events and the second event should be quality change.
    # Otherwise, it is malformed and should be filtered on the server

    currQuality = bevents[1].split(' : ')[1].split(' : ')[0]
    Buffering = True

    # bufferingLines represent when the video was buffering
    bufferingLines = []
    # playingLines represent when the video was playing
    playingLines = []
    # For each pair of events that happened during the streaming (except the last one, which is a special case)
    # There are the following possibilities
    # thefile = open(str(filename.replace('.png','.txt')), 'w')
    # thefile.write(str(bevents))

    for index in xrange(len(bevents)):
        event = bevents[index]
        # The next event
        if index == len(bevents) - 1:
            ntimeStamp = endtime
        else:
            ntimeStamp = float(bevents[index + 1].split(' : ')[-1])
        # If this event is buffering
        # Independent of the next event, add an additional line for this buffering event
        if 'Buffering' in event:
            Buffering = True
            timeStamp = float(event.split(' : ')[-1])
            bufferingLines.append(([timeStamp, ntimeStamp], [quality2y[currQuality], quality2y[currQuality]]))

        elif 'Quality change' in event:
            newQuality = event.split(' : ')[1]
            timeStamp = float(event.split(' : ')[-1])
            # Need to add a vertical line from currQuality to newQuality
            # Then a horizontal line until next event
            if Buffering:
                bufferingLines.append(([timeStamp, timeStamp], [quality2y[currQuality], quality2y[newQuality]]))
                bufferingLines.append(([timeStamp, ntimeStamp], [quality2y[newQuality], quality2y[newQuality]]))
            else:
                playingLines.append(([timeStamp, timeStamp], [quality2y[currQuality], quality2y[newQuality]]))
                playingLines.append(([timeStamp, ntimeStamp], [quality2y[newQuality], quality2y[newQuality]]))
            # update current quality
            currQuality = newQuality

        else:
            # An additional line for playing event
            Buffering = False
            timeStamp = float(event.split(' : ')[-1])
            playingLines.append(([timeStamp, ntimeStamp], [quality2y[currQuality], quality2y[currQuality]]))

    for bufferingLine in bufferingLines:
        print bufferingLine
        x1x2 = bufferingLine[0]
        y1y2 = bufferingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='r', linewidth=3, label="Buffering")

    for playingLine in playingLines:
        print playingLine
        x1x2 = playingLine[0]
        y1y2 = playingLine[1]
        if filename.split('_')[0] == 'ATT':
            plt.plot(x1x2, y1y2, 'k-', color='orange',  linestyle='--', alpha = 0.5, label=filename.split('_')[0]+"_Playing")
        if filename.split('_')[0] == 'TMobile':
            plt.plot(x1x2, y1y2, 'k-', color='purple', linestyle='--', label=filename.split('_')[0]+"_Playing")

        if filename.split('_')[0] == 'Verizon':
            plt.plot(x1x2, y1y2, 'k-', color='b',  linestyle='--', label=filename.split('_')[0]+"_Playing")
        if filename.split('_')[0] == 'WiFi':
            plt.plot(x1x2, y1y2, 'k-', color='g',  linestyle='--', label=filename.split('_')[0]+"_Playing")

    if contentprovider == 'youtube':
        ax.set_yticklabels(['', 'tiny', 'small', 'medium', 'large', '720P', '1080P', '1440'])
    if contentprovider == 'vimeo':
        ax.set_yticklabels(['', '270p', '360p', '540p', '720p', '1080p', '2K', '4K'])
    if contentprovider == 'netflix':
        ax.set_yticklabels(['', '100', '180', '240', '288', '384', '480', '720','1080','1400','2050'])        

    from collections import OrderedDict
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())

    plt.title('Comparison of quality changes of different providers in Youtube')
    plt.xlabel('Time (s)')
    plt.ylabel('Quality')

    # plt.show()
    # plt.savefig(filename + '.png')
    return plt


currdir = os.getcwd()
files = glob.glob(currdir+'/graphs/*/*.txt')
print files 
print '--------------'
endtime = 120
fig, ax = plt.subplots()
for file in files:
    with open(file, 'rb') as f:
        bevents = pickle.load(f)
    print bevents
    print type(bevents)
    plt = drawQualityChangeGraph(fig, ax, bevents, endtime, file.split('/')[8], 'youtube')

plt.show()