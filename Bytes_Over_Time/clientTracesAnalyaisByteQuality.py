'''
This is for analyzing packet traces collected on the client
Input : one pcap file, one
Output : the bytes/time graph for this recorded trace,
blue dots for the correctly received ones,
red Xs for the retransmitted ones,
yellow dots for the out-of-order ones,
green dots for the acknowledgement sent to the server
The background colors reflect the video quality being played
'''

import sys, subprocess, os, numpy
import matplotlib
import json

matplotlib.use('Agg')
import matplotlib.pyplot as plt


class Pac(object):
    def __init__(self, ts, psize, retrans):
        self.ts = float(ts)
        self.psize = int(psize)
        self.retrans = retrans

    def update(self, ts, psize, retrans):
        self.ts = float(ts)
        self.psize = int(psize)
        self.retrans = retrans


def GetPacLists(pcapFile, serverPort=None):
    if (serverPort is None):
        print 'Please provide server Port'
        sys.exit()

    src_port = 'tcp.srcport'
    dst_port = 'tcp.dstport'
    if 'QUIC' in pcapFile:
        src_port = 'udp.srcport'
        dst_port = 'udp.dstport'

    # ips = 'ip.src'
    # if ':' in serverIP:
    #     ips = 'ipv6.src'

    cmd = ['tshark', '-r', pcapFile, '-T', 'fields', '-E', 'separator=/t', '-e', src_port,
           '-e', dst_port, '-e', 'frame.time_relative', '-e', 'frame.len', '-e', 'tcp.analysis.retransmission']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()

    pacLists = {}

    for sl in output.splitlines():
        l = sl.split('\t')
        src_port = l[0]
        dst_port = l[1]
        # Get the info of this packet
        try:
            # time relative to the beginning of the connection
            time = l[2]
            # the size of this packet
            psize = l[3]
            retrans = l[4]
        except:
            continue
        # only cares about server -> client packets
        if src_port != serverPort:
            continue

        pac = Pac(time, psize, retrans)

        key_1 = (src_port, dst_port)
        key_2 = (dst_port, src_port)
        if key_1 in pacLists:
            pacLists[key_1].append(pac)
        elif key_2 in pacLists:
            pacLists[key_2].append(pac)
        else:
            pacLists[key_1] = [pac]

    return pacLists


def write_videostats(resolutions):
    quality_changes = []
    for i in resolutions:
        if i.split(' : ')[0] == 'Quality change':
            quality_changes.append(i)

    videoStats = {}
    videoStats['qualityChange'] = {} 
    print len(quality_changes)
    for i in xrange(len(quality_changes)):
        print quality_changes[i].split(' : '), i
        if i != len(quality_changes) - 1:
            event, quality, start_time = quality_changes[i].split(' : ')
            next_event, next_quality, next_start_time = quality_changes[i+1].split(' : ')
            if quality not in videoStats['qualityChange']:
                videoStats['qualityChange'][quality] = [[start_time,next_start_time]]
            else:
                videoStats['qualityChange'][quality].append([start_time,next_start_time])

        else:
            print 'ELSE'
            event, quality, start_time = quality_changes[i].split(' : ')
            if quality not in videoStats['qualityChange']:
                videoStats['qualityChange'][quality] = [[start_time,120.0]]
            else:
                videoStats['qualityChange'][quality].append([start_time,120.0])

    return videoStats # videoStats = {'qualityChange': {'large': [[0.0, 0.0],[10, 14]], 'hd1080': [[0.0, 7]], 'small': [[7, 10]]}}



def main():
    # three inputs
    # pcapFile
    # serverPort
    # qualityChange.json

    try:
        pcapFile = sys.argv[1]
        serverPort = sys.argv[2]
        qualityChangeFile = sys.argv[3]
        contentprovider = sys.argv[4]
    except:
        print('\r\n Please provide the pcap file, the server ports p, and the qualityChange json file as inputs: '
              '[pcapFile] [serverPort] [qualityChangeFile]... ')
        sys.exit()

    in_Colors = ['#fcbba1', '#a6bddb', '#a1d99b', '#d4b9da']
    re_Colors = ['#99000d', '#034e7b', '#005a32', '#91003f']

    # Step 1, plot the video quality changes

    matplotlib.rcParams.update({'font.size': 36})
    fig, ax = plt.subplots(figsize=(22, 8))

    # example quality change dictionary
    # qualityChange = {'hd1080': [[5, 8], [12, 16]], 'Buffering': [[8,12], [0,2]], 'small': [[2,5]], 'medium':[[16, 20]], 'hd720':[[20,30]]}

    bevents = []

    # open file and read the content in a list
    with open(qualityChangeFile, 'r') as filehandle:  
        for line in filehandle:
            # remove linebreak which is the last character of the string
            currentPlace = line[:-1]
            # add item to the list
            bevents.append(currentPlace)

    videoStats = write_videostats(bevents)
    print videoStats
    # videoStats = json.load(open(qualityChangeFile, 'r'))
    

    qualityChange = videoStats['qualityChange']
    allQualitiesColors = ['#4f4f4f', '#5f5f5f', '#6f6f6f', '#8f8f8f', '#afafaf', '#cfcfcf', '#DFDFDF']

    # if contentprovider == "Youtube":
    #     dicVideoQuality = {'240p': 1, '360p': 2, '480p': 3, '720p': 4, '1080p': 5}

    # if contentprovider == "Amazon":
    #     dicVideoQuality = {'v5': 1, 'v6': 2, 'v7': 3, 'v8': 4, 'v9': 5,  'v12':6} # For Amazon
    #     # dicVideoQuality  = {'': '', '1': u'480x200', '2': u'480x200', '3': u'512x208', '4': u'512x208', '5': u'640x272', '6': u'640x272', '7': u'704x296', '8': u'720x480', '9': u'960x400'} # android

    # if contentprovider == "Netflix":
    #     dicVideoQuality = {'256x192': 1 , '320x240': 2 ,'384x216': 3, '480x270': 4, '608x342':5, '768x432': 6,'640x480': 7, '720x480': 8,'960x540':9, '1280x720':10,'1920x1080':11}

    # sortedQualityChange = sorted(qualityChange.keys(), key=lambda x: dicVideoQuality[x])

    # qualityColors = allQualitiesColors[-len(sortedQualityChange):]
    # print('\r\n sorted quality change', qualityChange, sortedQualityChange, qualityColors)
    # # setting up the color bar on the right side of the graph
    # mymap = matplotlib.colors.ListedColormap(qualityColors)
    # Z = [[0, 0], [0, 0]]
    # min, max = (0, len(qualityColors))
    # step = 1
    # levels = range(min, max + step, step)
    # CS3 = plt.contourf(Z, levels, cmap=mymap)
    # plt.clf()
    # cbar = plt.colorbar(CS3)
    # if contentprovider == 'Amazon':
    #     convertor = {'v5': '512x213', 'v6': '652x272', 'v7': '710x296', 'v8': '710x296', 'v9': '1152x480', 'v12': '1280x533'}  #ios
    #     # android_convertor = {'1':'480x200', '2': '480x200', '3':'512x208', '4':'512x208', '5':'640x272', '6':'640x272', '7':'704x296', '8':'720x480', '9' : '960x400'}

    #     new_ticks = []
    #     for i in sortedQualityChange:
    #         try:
    #             new_ticks.append(convertor[i])
    #         except:
    #             new_ticks.append(android_convertor[i])
    #     cbar.ax.set_yticklabels(new_ticks)
    # else:
    #     cbar.ax.set_yticklabels(sortedQualityChange)

    # qualityCount = 0
    # for quality in sortedQualityChange:
    #     for interval in qualityChange[quality]:
    #         plt.axvspan(interval[0], interval[1], facecolor=qualityColors[qualityCount], lw=0)
    #     qualityCount += 1

    # Step 2, plot the packet traces

    # get one packet list for each connection (defined by 4 tuples)
    # Since srcIP and dstIP should already be filtered and unique
    # each connection can be defined by dst and src port
    # pacLists = {(tcp.src1, tcp.dst1) : packet_list1,
    # (tcp.src2, tcp.dst2) : packet_list2}
    # packet_list = [Pac1, Pac2], each Pac object has three values
    # Where ts is the timestamp, psize is the packet size,
    # retrans is the boolean shows whether this packet is a retransmission
    pacLists = GetPacLists(pcapFile, serverPort=serverPort)

    # combine packets from all lists
    # outcome should be two lists for first transmit and retransmission
    # each item in the lists is (ts, bytes_received)
    # where bytes_received is the total number of bytes received (retransmission excluded) at each point

    retrans_ts = []
    retrans_byte = []
    firstt_ts = []
    firstt_byte = []
    all_pacs_list = []

    for stream in pacLists:
        print(stream, len(pacLists[stream]))
        for pac in pacLists[stream]:
            all_pacs_list.append(pac)

    all_pacs_list.sort(key=lambda x: x.ts)
    # now all_pacs_list has all the packets from multiple connections combines
    # next step is to update the second value in the tuple from psize to bytes_received
    bytes_received = 0
    for pac in all_pacs_list:
        if pac.retrans:
            retrans_ts.append(pac.ts)
            retrans_byte.append(bytes_received)
        else:
            bytes_received += pac.psize
            firstt_ts.append(pac.ts)
            firstt_byte.append(bytes_received)

    plotting_dic = {}
    plotting_dic['firstt_byte'] = firstt_byte
    plotting_dic['firstt_ts'] = firstt_ts
    plotting_dic['retrans_ts'] = retrans_ts
    plotting_dic['retrans_byte'] = retrans_byte
    plotting_dic['qualityChange'] = qualityChange
    plotting_dic['server_port'] = serverPort
    plotting_dic['contentprovider'] = contentprovider
    plotting_dic['all_pacs_list'] = len(all_pacs_list)
    plotting_dic['fileName'] = pcapFile.split('.')[0].split('/')[-1]


    fileName = pcapFile.split('.')[0].split('/')[-1]
    print fileName , ' this is filename'
    with open(fileName+'.json', 'w') as fp:
        json.dump(plotting_dic, fp)

    plt.plot(firstt_ts, firstt_byte, 'o', markerfacecolor='none', markeredgewidth=3, markersize=15,
             markeredgecolor=in_Colors[0], label='First Arrival')
    plt.plot(retrans_ts, retrans_byte, 'x', markerfacecolor='none', markeredgewidth=3, markersize=15,
             markeredgecolor=re_Colors[0], label='Retrans')
    plt.ylim(0,60000000)
    plt.xlim(0,120)
    print(float(firstt_byte[-1]))
    print(float(firstt_ts[-1]))
    print(float(firstt_ts[-1]) * 8 / 10 ** 6)
    print(
        '\r\n goodput rate', float(firstt_byte[-1]) / float(firstt_ts[-1]) * 8 / 10 ** 6, len(firstt_ts),
        len(retrans_ts))
    retransmission_rate = float(len(retrans_ts)) / float(len(all_pacs_list))
    print('\r\n retransmission rate ', retransmission_rate)
    plt.legend(loc='upper right', markerscale=2, fontsize=30)

    plt.xlabel('Time (s)')
    plt.ylabel('Bytes')
    plt.tight_layout()
    plt.savefig('{}_Byte_Retrans_{}_Goodput_{}.png'.format(fileName,retransmission_rate,float(firstt_byte[-1]) / float(firstt_ts[-1]) * 8 / 10 ** 6), bbox_inches='tight')


if __name__ == "__main__":
    main()