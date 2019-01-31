## only works for android phones for youtube
from xml.dom import minidom
import glob
import re
import matplotlib.pyplot as plt
import random, string, os, sys

def random_ascii_by_size(size):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))


def drawQualityChangeGraph(bevents, endtime, filename):
    print '------------'
    fig, ax = plt.subplots()
    
    plt.ylim((0, 7))
    plt.xlim((0, endtime))
    plt.xlabel('Time')
    plt.ylabel('Video Quality')
    quality2y = {'':0, '256x144':1, '426x240':2, '640x360': 3, '854x480': 4, '1280x720':5, '1920x1080':6}

    ticks = ['','256x144','426x240', '640x360','854x480', '1280x720','1920x1080']

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
    ax.set_yticklabels(ticks)
    plt.title(filename.split('/')[-1])

    plt.savefig(filename + '.png')



try:
    network  = sys.argv[1]
except:
    print '\r\n Please provide one input : [the network being tested (e.g. WiFi?)]'
    sys.exit(-1)



bandwidths = []
resolutions = []
times = []
# parse an xml file by name
prev_time = 0
xml_files = glob.glob('*.xml')
print xml_files
xml_files.sort(key=lambda f: int(filter(str.isdigit, f)))
print xml_files
print '--------------------'
for xml in xml_files:
    print xml
    time = xml.split('_')[1].replace('.xml','')
    if prev_time == 0:
    	prev_time = time
    	
    times.append(float(time)-float(prev_time))

    mydoc = minidom.parse(xml)
    items = mydoc.getElementsByTagName('node')
    for elem in items:
	txt = (elem.attributes['text'].value)
	if txt != "":
	    # print txt
	    resolution = re.findall(r'video/mp4.*@',txt)
	    # bandwidth_mbps = re.findall(r'.*mbps', txt)
	    # bandwidth_kbps = re.findall(r'.*kbps', txt)
	    if len(resolution) > 0:
	    	print resolution
	    	resolutions.append(resolution[0].replace('video/mp4 ','').replace('@',''))

	    # if len(bandwidth_mbps) > 0:
	    	# bandwidth_mbps = float(bandwidth_mbps[0].replace(' ','').replace('mbps',''))
	    	# bandwidths.append(bandwidth_mbps*1000)
	    	# print bandwidth_mbps*1000
	    # if len(bandwidth_kbps) > 0:
	    	# print bandwidth_kbps[0].replace(' ','').replace('kbps','')
	    	# bandwidths.append(bandwidth_kbps[0].replace(' ','').replace('kbps',''))
	    # print bandwidth_kbps, bandwidth_mbps
    print '------------'



diff = len(times) - len(resolutions)
for i in xrange(diff):
	resolutions.append(resolutions[0])


# Right Rotating a list to n positions 
n = diff
resolutions = (resolutions[-n:] + resolutions[:-n]) 
print resolutions, len(resolutions)


bevents = ["Buffering : 0.0"]
bevents.append("Quality change : "+str(resolutions[0])+" : 0.0")
bevents.append("Playing : 0.0")

currQuality = resolutions[0]
for i in xrange(len(resolutions)):
	if currQuality != resolutions[i]:
		currQuality = resolutions[i]
		bevents.append("Quality change : "+str(resolutions[i])+" : "+str(times[i]))




print bevents

# write bevents to file
with open(network+"_youtube.txt", 'w') as f:
    for item in bevents:
        f.write("%s\n" % item)



endtime = 120
userID = random_ascii_by_size(10)
currdir = os.getcwd()
dirName = currdir + '/youtube_graphs/' + userID + '/'
if not os.path.isdir(dirName):
    os.makedirs(dirName)

graphTitle = '{}'.format(network)
filename = dirName + graphTitle + '_'  + '.png'
drawQualityChangeGraph(bevents, endtime, filename)
# resolution_labels = []


# for resolution in resolutions:
# 	resolution_labels.append(quality2y[resolution])


# print times, len(times)
# print resolutions, len(resolutions)
# print resolution_labels


# fig, ax = plt.subplots()
# ax.set_yticklabels(ticks)
# plt.plot(times, resolution_labels, label='TMobile')
# plt.legend()
# plt.ylim((0, 5))
# plt.xlabel('Time (s)')
# plt.ylabel('Bandwidth/Download Speed Kbps')
# plt.title('Download Speed of TMobile on the phone app')
# plt.show()
# print times
# # print bandwidths