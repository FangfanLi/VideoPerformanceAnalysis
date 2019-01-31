'''

Say you've done a bunch of pcaps in a folder (e.g. from Netflix streams). You need to run this:

    python Xputs_from_pcap.py 
    
This will write the throughputs of the pcap to file
'''

import subprocess, os, sys, numpy, random
import matplotlib.pyplot as plt
from scipy import interpolate, integrate
from scipy.stats import ks_2samp
import glob

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

def doXputsCDFplots(pcapFiles):
    colors = ['r', 'b', 'g', 'y', 'c']
    i      = -1
    for pcapFile in pcapFiles:
        i       += 1
        ts, xput = doXputs(pcapFile)
        # write bevents to file
        with open("CDF_Data/"+pcapFile.split('/')[-1].split('_')[0]+"_"+pcapFile.split('/')[-1].split('_')[1]+".txt", 'a') as f:
            for i in xput:
                f.write(str(i)+"\n")

        print '\r\n AVERAGE THROUGHPUT', numpy.average(xput)
        print '\r\n MAX THROUGHPUT', numpy.max(xput)

        # plt.plot(x, y, '-', color=colors[i%len(colors)], linewidth=2, label=pcapFile.rpartition('/')[2])

def main():
    inp = raw_input() # enter the experiments name
    for pcap in glob.glob('/Users/arian/Desktop/PCAP/bro/'+inp+'/Server/*pin.pcap'):
        print pcap
        doXputsCDFplots([pcap])
    

main()
