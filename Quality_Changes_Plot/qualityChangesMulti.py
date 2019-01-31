import random, string, os, sys
import matplotlib.pyplot as plt
import glob
import matplotlib
from collections import OrderedDict

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
def random_ascii_by_size(size):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))


def drawQualityChangeGraph(fig, ax, bevents, endtime, filename, contentprovider):
    matplotlib.rcParams.update({'font.size': 16})
    print '------------', contentprovider
    # fig, ax = plt.subplots()
    
    # for netflix it should be (0,9.5) since it has more yticks
    plt.ylim((0, 5.5))
    plt.xlim((0, endtime))
    # quality2y = {'':0, '256x144':1, '426x240':2, '640x360': 3, '854x480': 4, '1280x720':5, '1920x1080':6}
    # ticks = ['','256x144','426x240', '640x360','854x480', '1280x720','1920x1080']

    # create a case for each app/VPN pair so if they have the same resolution it wouldn't coincide.
    if contentprovider == "Amazon":
        quality2y = {'v5': 1, 'v6': 2, 'v7': 3, 'v8': 4, 'v9': 5, 'v12':6}

    if contentprovider == "Youtube":
        if filename.split('_')[1] == 'Sprint':
            if filename.split('_')[2] == 'VPN':
                quality2y = {'240p': 1.03, '360p': 2.03, '480p': 3.03, '720p': 4.03, '1080p': 5.03}
            else:
                quality2y = {'240p': 1.08, '360p': 2.08, '480p': 3.08, '720p': 4.08, '1080p': 5.08}

        if filename.split('_')[1] == 'ATT':
            if filename.split('_')[2] == 'VPN':
                quality2y = {'240p': 1.05, '360p': 2.05, '480p': 3.05, '720p': 4.05, '1080p': 5.05}
            else:
                quality2y = {'240p': 1.1, '360p': 2.1, '480p': 3.1, '720p': 4.1, '1080p': 5.1}

        if filename.split('_')[1] == 'Verizon':
            if filename.split('_')[2] == 'VPN':
                quality2y = {'240p': 1.0, '360p': 2.0, '480p': 3.0, '720p': 4.0, '1080p': 5.0}
            else:
                quality2y = {'240p': 1.05, '360p': 2.05, '480p': 3.05, '720p': 4.05, '1080p': 5.05}
                
        if filename.split('_')[1] == 'TMobile':
            if filename.split('_')[2] == 'VPN':
                quality2y = {'240p': 1.15, '360p': 2.15, '480p': 3.15, '720p': 4.15, '1080p': 5.15}
            else:            
                quality2y = {'240p': 1.2, '360p': 2.2, '480p': 3.2, '720p': 4.2, '1080p': 5.2}

        if filename.split('_')[1] == 'WiFi':
            if filename.split('_')[2] == 'VPN':
                quality2y = {'240p': 0.9, '360p': 1.9, '480p': 2.9, '720p': 3.9, '1080p': 4.9}
            else:
                quality2y = {'240p': 1.04, '360p': 1.94, '480p': 2.94, '720p': 3.94, '1080p': 4.94}


    if contentprovider == "Netflix":
        quality2y = {'320x240': 1 ,'384x216': 2, '480x270': 3, '608x342': 4 , '768x432': 5 ,'640x480': 6, '720x480': 7,'720x1280':8,'1920x1080':9}


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
        print event , ' event'
        # The next event
        if index == len(bevents) - 1:
            ntimeStamp = endtime
        else:
            # print bevents[index + 1].split(' : ')
            # print '-      -'
            ntimeStamp = float(bevents[index + 1].split(' : ')[-1])
        # If this event is buffering
        # Independent of the next event, add an additional line for this buffering event
        if 'Buffering' in event:
            Buffering = True
            timeStamp = float(event.split(' : ')[-1])
            bufferingLines.append(([timeStamp, ntimeStamp], [quality2y[currQuality], quality2y[currQuality]]))

        elif 'Quality change' in event:
            newQuality = event.split(' : ')[1]
            # print quality2y[newQuality], newQuality
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
        x1x2 = bufferingLine[0]
        y1y2 = bufferingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='r', linewidth=3)

    
    for playingLine in playingLines:
        print playingLine
        x1x2 = playingLine[0]
        y1y2 = playingLine[1]
        print filename.split('_')

        if filename.split('_')[1] == 'Sprint':
            if filename.split('_')[2] == 'VPN':
                plt.plot(x1x2, y1y2, 'k*', color='darkolivegreen',  linestyle='--', alpha = 0.8, label=filename.split('_')[1]+" VPN")
            else:
                plt.plot(x1x2, y1y2, 'k-', color='olive',  linestyle='solid', alpha = 0.8, label=filename.split('_')[1])

        if filename.split('_')[1] == 'ATT':
            if filename.split('_')[2] == 'VPN':
                plt.plot(x1x2, y1y2, 'k-', color='darkblue',  linestyle='--', alpha = 0.8, label=filename.split('_')[1]+" VPN")
            else:
                plt.plot(x1x2, y1y2, 'k-', color='blue',  linestyle='solid', alpha = 0.8, label=filename.split('_')[1])

        if filename.split('_')[1] == 'TMobile':
            if filename.split('_')[2] == 'VPN':
                plt.plot(x1x2, y1y2, 'k-', color='orchid', linestyle='dashdot',alpha = 0.8, label=filename.split('_')[1]+" VPN")
            else:
                plt.plot(x1x2, y1y2, 'k-', color='darkorchid', linestyle='solid', alpha = 0.8,label=filename.split('_')[1])

        if filename.split('_')[1] == 'Verizon':
            if filename.split('_')[2] == 'VPN':
                plt.plot(x1x2, y1y2, 'k^', color='darkred',  linestyle='--',alpha = 0.8, label=filename.split('_')[1]+" VPN")
            else:
                plt.plot(x1x2, y1y2, 'k-', color='r',  linestyle='solid',alpha = 0.8, label=filename.split('_')[1])
        if filename.split('_')[1] == 'WiFi':
            if filename.split('_')[2] == 'VPN':
                plt.plot(x1x2, y1y2, 'k-', color='darkgreen',  linestyle='dotted',alpha = 0.8, label=filename.split('_')[1]+" VPN")
            else:
                plt.plot(x1x2, y1y2, 'k-', color='g',  linestyle='solid', alpha = 0.8,label=filename.split('_')[1])

    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc='best',fontsize=14)

    plt.tight_layout()
    plt.xlabel('Time (s)',fontsize=14)
    plt.ylabel('Video Resolution',fontsize=14)

    if contentprovider == 'Youtube':
        ax.set_yticklabels(['', '240p', '360p', '480p', '720P', '1080p'])
    if contentprovider == 'Amazon':
        ax.set_yticklabels(['', '512x213', '652x272', '710x296', '710x296', '1152x480', '1280x533'])
    if contentprovider == 'Netflix':
        ax.set_yticklabels(['', '320x240' , '384x216',  '480x270', '608x342','768x432','640x480','720x480','720x1280','1920x1080'])
    return plt, by_label

def main():

    content_provider = 'Youtube'
    endtime = 120
    fig, ax = matplotlib.pyplot.subplots(figsize=(7, 5.1))

    userID = random_ascii_by_size(10)
    currdir = os.getcwd()
    dirName = currdir + '/amazon_graphs/' + userID + '/'
    if not os.path.isdir(dirName):
        os.makedirs(dirName)

    graphTitle = '{}'.format(content_provider)
    filename = dirName + graphTitle + '_'  + 'merged.png'

    # read the quality changes events
    for bevents_file in glob.glob('Bevents/bevents*.txt'):
        bevents = []
        
        with open(bevents_file, 'r') as filehandle:  
            for line in filehandle:
                currentPlace = line[:-1]
                bevents.append(currentPlace)
        # print bevents
        plt,by_label = drawQualityChangeGraph(fig, ax, bevents, endtime, bevents_file, content_provider)
    # plt.tight_layout()

    # manually re order legends
    plt.legend([by_label['ATT'],by_label['TMobile'],by_label['Verizon'],by_label['Sprint'],by_label['WiFi'],by_label['ATT VPN'],by_label['TMobile VPN'],by_label['Verizon VPN'],by_label['Sprint VPN'],by_label['WiFi VPN']], ['ATT','TMobile','Verzion','Sprint','WiFi','ATT VPN','TMobile VPN','Verizon VPN','Sprint VPN', 'WiFi VPN'], loc='lower center',fontsize=13,ncol=2)
    plt.savefig('{}_Quality_Changes.png'.format(content_provider), bbox_inches='tight')    
    # plt.show()


if __name__ == "__main__":
    main()
