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

import time, sys, os, random, string, subprocess, urllib2, json, urllib, numpy
import sys, subprocess, os, numpy
import matplotlib
import json
import re
import urllib
from intervaltree import Interval, IntervalTree
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import itertools
import xmltodict


# try:
#     import seaborn as sns; sns.set()
# except ImportError:
#     pass

def random_ascii_by_size(size):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))


def drawQualityChangeGraph(bevents, endtime, filename,operating_system):
    print '------------'
    fig, ax = plt.subplots()
    
    plt.ylim((0, 7))
    plt.xlim((0, endtime))
    plt.xlabel('Time')
    plt.ylabel('Video Quality')
    quality2y = {'v5': 1, 'v6': 2, 'v7': 3, 'v8': 4, 'v9': 5, 'v10': 6,'v11':7}

    ticks , quality2y = find_quality(operating_system)
    print quality2y
    print 'ticks are'
    print ticks

    # quality2y = {'v5': 1, 'v6': 2, 'v7': 3, 'v8': 4}
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
    for index in xrange(len(bevents)):
        event = bevents[index]
        print event
        # The next event
        if index == len(bevents) - 1:
            ntimeStamp = endtime
        else:
            print bevents[index + 1].split(' : ')
            ntimeStamp = float(bevents[index + 1].split(' : ')[-1])
        # If this event is buffering
        # Independent of the next event, add an additional line for this buffering event
        if 'Buffering' in event:
            Buffering = True
            timeStamp = float(event.split(' : ')[-1])
            bufferingLines.append(([timeStamp, ntimeStamp], [quality2y[currQuality], quality2y[currQuality]]))

        elif 'Quality change' in event:
            
            newQuality = event.split(' : ')[1]
            print quality2y[newQuality], newQuality
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
        plt.plot(x1x2, y1y2, 'k-', color='r', linewidth=3)

    for playingLine in playingLines:
        print playingLine
        x1x2 = playingLine[0]
        y1y2 = playingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='b')

    # ax.set_yticklabels(['', '240', '360', '480', '720', '1080', '1440'])
    ax.set_yticklabels(ticks.values())
    plt.title(filename.split('/')[-1])

    plt.savefig(filename + '.png')


def find_quality(operating_system):
    print 'find quality --------------------'
    dicVideoQuality = {'':''}
    dicVideoVersion = {'v0':''}

    cnt = 1
    # link = "http://s3.ll.hls.us.aiv-cdn.net/d/2$4Bv0-QUJGWcgoYKcPUS1HR_Ljo8~/b73b/7c6c/bfaa/4482-9f1c-4dba914b033b/3f9adafa-840e-4055-99b0-59102612f93b.m3u8"
    link = "http://s3.ll.hls.us.aiv-cdn.net/d/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8"# baywatch from Verizon and WiFi
    # link = "http://11s3.lvlt.hls.us.aiv-cdn.net/d/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/prod/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" # verizon better

    # link = "http://a576avodhlss3us-a.akamaihd.net/d/2$eylY9uPqTbZsQF7mnUl9XGbOYpU~/ondemand/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" # baywatch from ATT
    # link = "http://djmcau1gdkhrg.cloudfront.net/dm/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" # baywatch tmobile
    #android
    # link = "http://a206avoddashs3ww-a.akamaihd.net/d/2$c9OlQMPGFNIvCTt6PKEcd7wOMbQ~/ondemand/iad_2/0281/f4ab/72db/4163-84ee-7e565919fe2d/5e26092b-e30e-4310-a019-32b1a89442c4_corrected.mpd"  # ATT
    # link = "http://s3-iad-2.cf.dash.row.aiv-cdn.net/dm/2$c9OlQMPGFNIvCTt6PKEcd7wOMbQ~/0281/f4ab/72db/4163-84ee-7e565919fe2d/5e26092b-e30e-4310-a019-32b1a89442c4_corrected.mpd" #TMobile Verizon
    link = "http://s3-iad-2.cf.hls.row.aiv-cdn.net/dm/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" # VPN ATT
    # link = "http://s3-iad-2.cf.hls.row.aiv-cdn.net/dm/2$yA9WQbAUYyk5Tgekt4NweWvztTA~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" # WiFi VPN
    link = "http://s3.ll.hls.row.aiv-cdn.net/d/2$yA9WQbAUYyk5Tgekt4NweWvztTA~/iad_2/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" #WifI throttle
    link = "http://s3-iad-2.cf.hls.row.aiv-cdn.net/dm/2$yA9WQbAUYyk5Tgekt4NweWvztTA~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" #WifI throttle 1.5
    link = "http://a34avodhlss3ww-a.akamaihd.net/d/2$89q0zhlxAEokTg4l2otZYBR1QSU~/ondemand/iad_2/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8"
    link = "http://s3-iad-2.cf.hls.row.aiv-cdn.net/dm/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" #ATT w/o streamsaver
    link = "http://a34avodhlss3ww-a.akamaihd.net/d/2$eylY9uPqTbZsQF7mnUl9XGbOYpU~/ondemand/iad_2/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" 
    link = "http://7s3.lvlt.hls.row.aiv-cdn.net/d/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/prod/iad_2/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8"
    link = "http://s3-iad-2.cf.hls.row.aiv-cdn.net/dm/2$B7J7_AW_nj8FHgG2Zdkscm3K22g~/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62.m3u8" 
    f = urllib.urlopen(link)

    myfile = f.readlines()
    itfile = iter(myfile)
    for line in itfile:
        if operating_system == 'ios':
            if 'CLOSED-CAPTIONS' in line:
                line = line.replace('\n','')+itfile.next()
            resolution_text = re.findall('RESOLUTION.*m3',line)
            if len(resolution_text) > 0:
                resolution_text = resolution_text[0]
                resolution = re.findall('RESOLUTION.*,F',resolution_text)
                version = re.findall('v[0-9]+.m3',resolution_text)
                print 'version in find quality', version
                if len(resolution) > 0:
                    resolution = re.findall('=.*,',resolution[0])[0].replace('=','').replace(',','')
                    dicVideoQuality[cnt] = resolution
                    # dicVideoVersion[version[0].replace('.m3','')] = resolution
                    dicVideoVersion[version[0].replace('.m3','')] = cnt
                    cnt += 1
        if operating_system == 'android':
            dicVideoVersion = {'0':''}
            f = urllib.urlopen(link)
            document = f.read()
            doc = xmltodict.parse(document)
            for i in doc['MPD']['Period']['AdaptationSet'][0]['Representation']:
                resolution_text = i['@width'] + 'x' + i['@height']
                version = i['BaseURL'].split('_')[2].replace(".mp4","")
                dicVideoQuality[cnt] = resolution_text
                dicVideoVersion[version] = cnt
                cnt += 1



    print dicVideoQuality
    print dicVideoVersion
    return dicVideoQuality, dicVideoVersion

def find_byte_quality(carrier, operating_system):
    if operating_system == 'android':
        print 'find byte quality---------------------'
        version_byte_seconds = {}
        link = "http://a206avoddashs3ww-a.akamaihd.net/d/2$c9OlQMPGFNIvCTt6PKEcd7wOMbQ~/ondemand/iad_2/0281/f4ab/72db/4163-84ee-7e565919fe2d/5e26092b-e30e-4310-a019-32b1a89442c4_corrected.mpd" #android
        link = "http://s3-iad-2.cf.dash.row.aiv-cdn.net/dm/2$c9OlQMPGFNIvCTt6PKEcd7wOMbQ~/0281/f4ab/72db/4163-84ee-7e565919fe2d/5e26092b-e30e-4310-a019-32b1a89442c4_corrected.mpd" # TMobile
        f = urllib.urlopen(link)
        document = f.read()
        doc = xmltodict.parse(document)
        
        for i in doc['MPD']['Period']['AdaptationSet'][0]['Representation']:
            start_time = 0.0
            print i['SegmentList']['@duration'], i['SegmentList']['@timescale']
            seconds_range = float(i['SegmentList']['@duration']) / float(i['SegmentList']['@timescale'])
            # print seconds_range
            print i['BaseURL'].split('_')
            version = i['BaseURL'].split('_')[2].replace(".mp4","")
            for byte in i['SegmentList']['SegmentURL']:
                byte_range = byte['@mediaRange']
                print byte_range, version, seconds_range
                end_time = start_time + int(float(seconds_range))
                if version not in version_byte_seconds:
                    version_byte_seconds[version] = {}
                if byte_range not in version_byte_seconds[version]:
                    version_byte_seconds[version][byte_range] = 0
                version_byte_seconds[version][byte_range] = str(start_time)+','+str(end_time)
                start_time = end_time



    if operating_system == 'ios':
        print 'find byte quality------------ ios ---------'
        f = open('/Users/arian/Desktop/PCAP/bro/http.log','r')
        lines = f.readlines()
        version_byte_seconds = {}
        for line in lines:
            if len(re.findall('v[0-9]+.m3u8',line)) > 0:
                attributes = line.split('\t')
                print attributes, 'attrbutes'
                host = attributes[8]
                path = attributes[9]
                url = 'http://' +host + path
                print url, 'url'
                f = urllib.urlopen(url)
                start_time = 0.0
                itfile = iter(f.readlines())
                # version = path.split('_')[1].split('.')[0]
                version = path.split('_')[-1].split('.')[0]
                print version, 'version'
                for line in itfile:
                    if carrier == 'ATT':
                        #EXTINF:3.294959, no desc #EXT-X-BYTERANGE:180856@281185208
                        if 'EXTINF' in line:
                            line = line.replace('\n',' ')+itfile.next()
                            # print line

                            seconds_range = re.findall('[0-9]+.*, ',line)[0].replace(', ','')
                            bytes_amount, start = line.split('BYTERANGE:')[1].split('@')
                            start = int(start.replace('\n',''))


                            byte_range = str(start)+'-'+str(start+int(bytes_amount)-1)
                            end_time = start_time + int(float(seconds_range))
                            if version not in version_byte_seconds:
                                version_byte_seconds[version] = {}
                            if byte_range not in version_byte_seconds[version]:
                                version_byte_seconds[version][byte_range] = 0
                            version_byte_seconds[version][byte_range] = str(start_time)+','+str(end_time)
                            start_time = end_time
                    else:
                        ##EXTINF:4.963292, no desc http://djmcau1gdkhrg.cloudfront.net/79df/dc30/b11f/4d48-a8d9-7be4848347e3/6ca0e01c-0322-46d3-8400-13c604e74c62_v9.ts/range/856725024-857814295
                        print 'line is ,', line

                        if 'EXTINF' in line:
                            line = line.replace('\n',' ')+itfile.next()
                            seconds_range = re.findall('[0-9]+.*, ',line)[0].replace(', ','')
                            byte_range = line.split('_v')[1]
                            # print byte_range, 'byte range'


                            version = 'v'+byte_range.split('.ts')[0]
                            byte_range = byte_range.split('/')[-1].replace('\n','')
                            print '------'
                            print version, byte_range
                            # end_time = start_time + float(seconds_range)
                            end_time = start_time + int(float(seconds_range))
                            
                            # print version, byte_range, seconds
                            if version not in version_byte_seconds:
                                version_byte_seconds[version] = {}
                            if byte_range not in version_byte_seconds[version]:
                                version_byte_seconds[version][byte_range] = 0
                            version_byte_seconds[version][byte_range] = str(start_time)+','+str(end_time)
                            start_time = end_time

    print 'END find byte ------------------------'
    return version_byte_seconds

def create_qualityChangeFile(carrier,operating_system):
    print 'create quality change file ---'
    if operating_system == 'android':
        if carrier == 'ATT':
            # tshark  -T fields -E separator="|" -e http.request.line -e http.request.uri -r amazon_ATT_2min.pcap > att_pcap.txt
            f = open('/Users/arian/Desktop/PCAP/android/att_pcap.txt','r') 
            bytes_version = {}
            lines = f.readlines()
            version_byte_seconds = {}
            first_playing_quality = ''
            flag_first_playing = 0

            for line in lines:
                if len(re.findall('video.',line)) > 0:
                    byte_text , version_text = line.split('|')
                    print version_text, line
                    try:
                        version = version_text.split('_')[3].replace('.mp4','').replace('\\','').replace('\n','')
                    except:
                        version = version_text.split('_')[2].replace('.mp4','').replace('\\','').replace('\n','')
                    byte_range = byte_text.split('bytes=')[1].split(',Accept')[0]
                    print version , byte_range
                    if version not in bytes_version:
                        bytes_version[version] = []
                    bytes_version[version].append(byte_range)
                    if flag_first_playing == 0:
                        first_playing_quality = version
                        flag_first_playing = 1


    if operating_system == 'ios':    
        if carrier == 'ATT':
            print 'ios , att'
            # tshark  -T fields -E separator="|" -e http.request.line -e http.request.uri -r amazon_ATT_2min.pcap > att_pcap.txt
            f = open('/Users/arian/Desktop/PCAP/bro/att_pcap.txt','r') 
            bytes_version = {}
            lines = f.readlines()
            version_byte_seconds = {}
            for line in lines:
                if len(re.findall('.ts',line)) > 0:
                    byte_text , version_text = line.split('|')
                    print line
                    print ' - = '
                    print version_text.split('_v')
                    version = 'v'+version_text.split('_v')[1].replace('.ts','').replace('\n','')[:1]
                    print version, ' verison'


                    print byte_text 


                    byte_range = byte_text.split('bytes=')[1].split(',Accept')[0]
                    # print version , byte_range
                    if 'v' in version:
                        if version not in bytes_version:
                            bytes_version[version] = []
                        bytes_version[version].append(byte_range)

        else:
            f = open('/Users/arian/Desktop/PCAP/bro/http.log','r')
            bytes_version = {}
            lines = f.readlines()
            version_byte_seconds = {}
            for line in lines:
                if len(re.findall('range',line)) > 0:
                    if len(re.findall('.ts',line)) > 0:
                        attributes = line.split('\t')
                        host = attributes[8]
                        path = attributes[9]
                        url = 'http://' +host + path

                        url = url.split('/')
                        print url, ' url'
                        version = url[-3].split('_')[1].replace('.ts','')
                        byte_range = url[-1] #last element is the byterange
                        # print version , byte_range
                        if 'v' in version:
                            if version not in bytes_version:
                                bytes_version[version] = []
                            bytes_version[version].append(byte_range)

    manifest_version_byte_seconds = find_byte_quality(carrier, operating_system)
    print manifest_version_byte_seconds.keys()
    print '----------------'
    version_interval = {}
    bevents = []


    for version in bytes_version:
        # tree = IntervalTree()
        tree = np.array([])
        print version, ' version'
        for byte_range in bytes_version[version]:
            print byte_range, manifest_version_byte_seconds[version][byte_range]
            start, end = manifest_version_byte_seconds[version][byte_range].split(',')
            start = int(float(start))
            end = int(float(end))

            tree = np.concatenate((tree,range(int((start)),int(float(end))+1, 1)),axis=0)
            # tree.addi(float(start), float(end)+0.0001)

        version_interval[version] = tree

    for i in list(itertools.combinations(version_interval.keys(),2)):
        x =  set(version_interval[i[0]]).intersection(set(version_interval[i[1]]))
        y = len(x)
        if len(x) > 0:
            print i[0],i[1], x
            for change in sorted(x):
                print change, 'change'
                bevents.append({'QualityChange' : str(i[0])+','+str(i[1]), 'change':(change)})
                # 
    bevents_list = []
    for i in sorted(bevents, key = lambda i: i['change']) :
        bevents_list.append('QualityChange : '+i['QualityChange']+' - '+str(i['change']))

    if operating_system == 'android':
        if first_playing_quality != '':
            bytes_version[first_playing_quality] = '0-0'

    # print version_interval
    print bevents_list
    return bytes_version, bevents_list

def main():
    try:
        network  = sys.argv[1]
        operating_system = sys.argv[2]
    except:
        print '\r\n Please provide one input : [the network being tested (e.g. WiFi?)]'
        sys.exit(-1)


    # three inputs
    # pcapFile
    # serverPort
    # qualityChange.json
    # print 'main'
    # t , quality2y = find_quality('android')
    # print t, quality2y
    # print '-------'
    # manifest_version_byte_seconds = find_byte_quality('ATT')
    print '======'
    bytes_version , quality_change = create_qualityChangeFile(network, operating_system)
    print '................................'
    # print quality_change
    # print 'end'
    version_interval = {}
    bevents = ["Buffering : 0.0"]
    first_time_event = 1
    current_quality = ''
    for version in bytes_version:
        print bytes_version[version]
        for time in bytes_version[version]:
            if time.split('-')[0] == '0':
                print version
                current_quality = version
                bevents.append("Quality change : "+str(version)+" : 0.0")
                break
    bevents.append("Playing : 0.0")
    for change_times in quality_change:
        v1,v2 = change_times.split(':')[1].split('-')[0].split(',')
        time = change_times.split('-')[1]

        if str(v1.strip()) == current_quality:
            current_quality = str(v2.strip())
            
            # time_slider = float(time.strip()) - time_slider
            print v1 , '->' , v2, time

            bevents.append("Quality change : " + v2.strip() + " : " +time.strip() ) 
        else:
            current_quality = str(v1.strip())
            
            # time_slider = float(time.strip()) - time_slider
            print v2 , '->' , v1, time

            bevents.append("Quality change : " + v1.strip() + " : "+time.strip() ) 
        print 'curr quality  : ', current_quality


    userID = random_ascii_by_size(10)
    currdir = os.getcwd()
    dirName = currdir + '/graphs/' + userID + '/'
    # make directory for
    if not os.path.isdir(dirName):
        os.makedirs(dirName)
    graphTitle = '{}'.format(network)
    count = 0
    stoptime = 180

    # a = [['Buffering : 0.0', 'Quality change : v8 : 0.0', 'Playing : 0.0', 'Quality change : v6 : 70.0', 'Quality change : v5 : 128.0']]

    print '>>>>>>>>>>>>>>>>>>>>>>>.'
    # print a
    print [bevents]
    print '>>>>>>>>>>>>>>>>>>>>>>>.'

    # write bevents to file
    with open("bevents_"+network+"_amazon.txt", 'w') as f:
        for item in bevents:
            f.write("%s\n" % item)



    for event in [bevents]:
        print event
        filename = dirName + graphTitle + '_' + str(count) + '.png'
        drawQualityChangeGraph(event, float(stoptime), filename,operating_system)
        count += 1
if __name__ == "__main__":
    main()
