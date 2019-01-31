'''

Say you've done a bunch of pcaps in a folder (e.g. from Netflix streams). You need to run this:

    python plotXputs.py pcap1 pcap2 ...
    
This will plot CDF plots of throughputs for all pcaps
'''

import subprocess, os, sys, numpy, random
import matplotlib.pyplot as plt
from scipy import interpolate, integrate
from scipy.stats import ks_2samp


def doXputs(pcapFile, xputInterval=0.25):
    #Run tshark

    # Use fixed number of buckets

    dcmd         = ['tshark', '-r', pcapFile, '-T', 'fields', '-e', 'frame.time_relative']
    dp           = subprocess.Popen(dcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    doutput, derr = dp.communicate()
    # tshark -r <filename> -R "tcp.stream eq <index>" -T fields -e frame.time_epoch
    duration = doutput.splitlines()[-1]
    # Dynamic xputInterval = (replay duration / # buckets)
    xputInterval = float(duration)/100


    cmd         = ['tshark', '-r', pcapFile, '-qz', 'io,stat,'+str(xputInterval)]
    p           = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    
    #Parse tshark output
    lines       = output.splitlines()
    end         = lines[4].partition('Duration:')[2].partition('secs')[0].replace(' ', '')
    lines[-2]   = lines[-2].replace('Dur', end)

    ts   = []
    xput = []


    for l in lines:
        if '<>' not in l:
            continue

        l      = l.replace('|', '')
        l      = l.replace('<>', '')
        parsed = map(float, l.split())
        
        start  = float(parsed[0])
        end    = float(parsed[1])
        dur    = end - start

        # if dur == 0 or ((float(parsed[-1])/dur)*8/1000000.0 > 23):
        if dur == 0:
            continue
        
        ts.append(end)
        xput.append(float(parsed[-1])/dur)

    xput = map(lambda x: x*8/1000000.0, xput)

    # print '\r\n XPUT',xput[:-1]
    # print '\r\n DDDDU', ts[:-1]

    print ts[:-1]
    print xput[:-1]
    return ts[:-1], xput[:-1]

def list2CDF(myList):
    myList = sorted(myList)
    
    x   = [0]
    y   = [0]
    
    for i in range(len(myList)):
        x.append(myList[i])
        y.append(float(i+1)/len(myList))
    
    return x, y

def doXputsCDFplots(pcapFiles, title=False):
    colors = ['r', 'b', 'g', 'y', 'c']
    i      = -1

    xputs = {}
    for pcapFile in pcapFiles:
        i       += 1
        ts, xput = doXputs(pcapFile)
        print '\r\n AVERAGE THROUGHPUT', numpy.average(xput)
        print '\r\n MAX THROUGHPUT', numpy.max(xput)
        x, y     = list2CDF(xput)
        plt.plot(x, y, '-', color=colors[i%len(colors)], linewidth=2, label=pcapFile.rpartition('/')[2])
        xputs[pcapFile] = xput


    plt.legend(loc='best', prop={'size':8})
    plt.grid()
    plt.xlabel('Xput (Mbits/sec)')
    plt.ylabel('CDF')
    plt.ylim((0, 1.1))

    # plt.annotate(result[0] + result[1])

    if title:
        plt.title(title)
    # plt.show()
    # plt.savefig(pcapFile+'_xputCDF.png')


doXputsCDFplots(sys.argv[1:])

