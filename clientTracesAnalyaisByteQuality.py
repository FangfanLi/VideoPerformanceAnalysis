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


# try:
#     import seaborn as sns; sns.set()
# except ImportError:
#     pass

def list2CDF(myList):
    myList = sorted(myList)

    x = [0]
    y = [0]

    for i in range(len(myList)):
        x.append(myList[i])
        y.append(float(i + 1) / len(myList))

    return x, y


def doXputsCDFplots(xputs, title=''):
    # inputs should be a dictionary key : input label; value : xput(goodput) list
    matplotlib.rcParams.update({'font.size': 13})
    fig, ax = plt.subplots()
    colors = ['#e41a1c', '#ff7f00', '#4daf4a', '#a65628', '#377eb8', '#ffff33', '#984ea3', '#f781bf']
    i = 0

    # cdfXputs = {}
    for xput in xputs:
        axput = float(sum(xputs[xput])) / float(len(xputs[xput]))
        axput = "{0:.2f}".format(axput)
        non_zero_xputs = [x for x in xputs[xput] if x > 0]
        title += '_' + xput + '_' + axput
        x, y = list2CDF(non_zero_xputs)
        plt.plot(x, y, '-', color=colors[i % len(colors)], linewidth=2, label=xput + '_' + axput + ' Mbps')
        i += 1

    plt.legend(loc='best')
    plt.grid()
    plt.xlabel('Download speed (Mbits/sec)')
    plt.ylabel('CDF')
    plt.ylim((0, 1.1))

    # if title:
    #     plt.title(title)

    fig.tight_layout()
    plt.savefig(title + '_CDF.png')
    plt.cla()
    plt.clf()
    plt.close()


def doXputs(timeL, packetL):
    # Run tshark

    packetL = [int(x) for x in packetL]
    timeL = [float(x) for x in timeL]

    # Use fixed number of buckets (100) for now
    numBuckets = 100

    # tshark -r <filename> -R "tcp.stream eq <index>" -T fields -e frame.time_epoch
    duration = timeL[-1]
    # Dynamic xputInterval = (replay duration / # buckets)
    xputInterval = float(duration) / numBuckets

    untilT = xputInterval
    xputs = []
    tbytes = 0
    for i in xrange(len(timeL)):
        # Calculate bytes for this period
        if timeL[i] >= untilT:
            xputs.append(tbytes / xputInterval)
            untilT += xputInterval
            tbytes = 0
        else:
            tbytes += packetL[i]

    xputs = map(lambda x: x * 8 / 1000000.0, xputs)

    return xputs


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


def main():
    # three inputs
    # pcapFile
    # serverPort
    # qualityChange.json

    try:
        pcapFile = sys.argv[1]
        serverPort = sys.argv[2]
        qualityChangeFile = sys.argv[3]
    except:
        print('\r\n Please provide the pcap file, the server ports p, and the qualityChange json file as inputs: '
              '[pcapFile] [serverPort] [qualityChangeFile]... ')
        sys.exit()

    in_Colors = ['#fcbba1', '#a6bddb', '#a1d99b', '#d4b9da']
    re_Colors = ['#99000d', '#034e7b', '#005a32', '#91003f']

    # Step 1, plot the video quality changes

    matplotlib.rcParams.update({'font.size': 36})
    fig, ax = plt.subplots(figsize=(22, 8), dpi=1080)

    # example quality change dictionary
    # qualityChange = {'hd1080': [[5, 8], [12, 16]], 'Buffering': [[8,12], [0,2]], 'small': [[2,5]], 'medium':[[16, 20]], 'hd720':[[20,30]]}

    videoStats = json.load(open(qualityChangeFile, 'r'))
    qualityChange = videoStats['qualityChange']
    allQualitiesColors = ['#4f4f4f', '#5f5f5f', '#6f6f6f', '#8f8f8f', '#afafaf', '#cfcfcf', '#ffffff']

    dicVideoQuality = {"BUFFERING": 1,
                       "tiny": 2,
                       "240": 2,
                       "small": 3,
                       "288": 3,
                       "384": 4,
                       "medium": 4,
                       "480": 5,
                       "large": 5,
                       "720": 6,
                       "hd720": 6,
                       "1080": 7,
                       "hd1080": 7}

    sortedQualityChange = sorted(qualityChange.keys(), key=lambda x: dicVideoQuality[x])

    qualityColors = allQualitiesColors[-len(sortedQualityChange):]
    print('\r\n sorted quality change', qualityChange, sortedQualityChange, qualityColors)
    # setting up the color bar on the right side of the graph
    mymap = matplotlib.colors.ListedColormap(qualityColors)
    Z = [[0, 0], [0, 0]]
    min, max = (0, len(qualityColors))
    step = 1
    levels = range(min, max + step, step)
    CS3 = plt.contourf(Z, levels, cmap=mymap)
    plt.clf()
    cbar = plt.colorbar(CS3)
    cbar.ax.set_yticklabels(sortedQualityChange)

    qualityCount = 0
    for quality in sortedQualityChange:
        for interval in qualityChange[quality]:
            plt.axvspan(interval[0], interval[1], facecolor=qualityColors[qualityCount], lw=0)
        qualityCount += 1

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

    fileName = pcapFile.split('.')[0].split('/')[-1]

    plt.plot(firstt_ts, firstt_byte, 'o', markerfacecolor='none', markeredgewidth=3, markersize=15,
             markeredgecolor=in_Colors[0], label='First Arrival')
    plt.plot(retrans_ts, retrans_byte, 'x', markerfacecolor='none', markeredgewidth=3, markersize=15,
             markeredgecolor=re_Colors[0], label='Retrans')

    print(
        '\r\n goodput rate', float(firstt_byte[-1]) / float(firstt_ts[-1]) * 8 / 10 ** 6, len(firstt_ts),
        len(retrans_ts))
    plt.legend(loc='lower right', markerscale=2, fontsize=30)

    plt.xlabel('Time (s)')
    plt.ylabel('Bytes')
    plt.tight_layout()
    plt.savefig('{}_Byte.png'.format(fileName), bbox_inches='tight')


if __name__ == "__main__":
    main()
