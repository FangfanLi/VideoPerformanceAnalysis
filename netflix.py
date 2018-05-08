from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import os
import sys
import requests
import json
import random
import time, sys, os, random, string, subprocess, urllib2, json, urllib, numpy
import re
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
import matplotlib.pyplot as plt
import pickle


try:
    network  = sys.argv[1]
    tether = sys.argv[2]
    browser = sys.argv[3]
    testID = sys.argv[4]
    videoID = sys.argv[5]
    # contentprovider = sys.argv[6]
    contentprovider = 'netflix'
except:
    print '\r\n Please provide 6 inputs : [the network being tested (e.g. WiFi?)] [are you tethered (YES or NO)] [which browser to use (Firefox or Chrome)] [the test ID] [videoID to stream] ['
    sys.exit(-1)
doGraphs = True

def getQualityPercentage(qualities):
    rQualities = {}
    for quality in qualities:
        if rQualities.has_key(quality):
            rQualities[quality] += 1
        else:
            rQualities[quality] = 1

    for quality in rQualities:
        rQualities[quality] = "{0:.2f}".format(float(rQualities[quality])/float(len(qualities)))

    return rQualities


def getQualityPeriod(multiTestsQualities):
    rQualities = {}
    numTests = len(multiTestsQualities)
    for singleTestQualities in multiTestsQualities:
        for quality in singleTestQualities.keys():
            if not rQualities.has_key(quality):
                rQualities[quality] = 0
            rQualities[quality] += singleTestQualities[quality]

    for quality in rQualities:
        rQualities[quality] = round(rQualities[quality]/float(numTests),2)

    return rQualities


def drawQualityChangeGraph(bevents, endtime, filename):
    fig, ax = plt.subplots()
    plt.ylim((0, 9))

    plt.xlim((0, endtime))
    plt.xlabel('Time')
    plt.ylabel('Video Quality')
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
        x1x2 = bufferingLine[0]
        y1y2 = bufferingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='r', linewidth=3)

    for playingLine in playingLines:
        x1x2 = playingLine[0]
        y1y2 = playingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='b')

    ax.set_yticklabels(['', '100', '180', '240', '288' ,'384', '480', '720P', '1080P', '1400', '2050'])

    plt.title(filename.split('/')[-1])

    plt.savefig(filename + '.png')



class analyzerI(object):
    '''
    This class contains all the methods to interact with the analyzer server
    '''
    def __init__(self, ip, port):
        self.path = ('http://'
                     + ip
                     + ':'
                     + str(port))

    def getSingleResult(self, userID):
        '''
        Send a GET request to get result for a given userID
        '''
        # userID specifies the test
        data = {'userID':userID}

        res = self.sendRequest('GET',data=data)
        return res

    def sendRequest(self, method, data=''):
        '''
        Sends a single request to analyzer server
        '''
        data = urllib.urlencode(data)

        if method.upper() == 'GET':
            req = urllib2.Request(self.path + '?' + data)

        elif method.upper() == 'POST':
            req  = urllib2.Request(self.path, data)

        res = urllib2.urlopen(req).read()
        return json.loads(res)



def random_ascii_by_size(size):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))



if browser == 'Chrome':
    # userDir       = 'UserDir'
    # chromeOptions = webdriver.ChromeOptions()
    # options       = ['--user-data-dir={}'.format(userDir), '--disable-background-networking', '--disable-default-apps', '--disable-extensions']

    # for o in options:
    #     chromeOptions.add_argument(o)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--enable-quic")
    driver = webdriver.Chrome('/Users/arian/Desktop/WeHe/VideoPerformanceAnalysis/chromedriver', chrome_options = chrome_options)

elif browser == 'Firefox':
    driver = webdriver.Firefox(executable_path='/Users/arian/Desktop/WeHe/VideoPerformanceAnalysis/geckodriver')
else:
    print '\r\n Please specify a valid browser to us [Chrome OR Firefox]'
    sys.exit(-1)



# driver = webdriver.Firefox(executable_path='/Users/arian/Desktop/VideoPerformanceAnalysis/geckodriver')
driver.get("https://www.netflix.com")
login = driver.find_element_by_css_selector(".authLinks.signupBasicHeader")
login.click()
element = driver.find_element_by_name("email")
element.send_keys("negargh@uci.edu")
# element.send_keys("arianniaki@gmail.com")
submit = driver.find_element_by_css_selector(".btn.login-button.btn-submit.btn-small")
submit.click()
element2 = driver.find_element_by_name("password")
element2.send_keys("123456m.")

submit2 = driver.find_element_by_css_selector(".btn.login-button.btn-submit.btn-small")
print 'waited'
submit2.click()
# open the play page
driver.get("https://www.netflix.com/watch/"+videoID)

driver.execute_script("console.log('wow');")

print 'bye'
counter = 0
cond = True
events = []
stoptime = 120
prev_player_state = ''
prev_quality = ''


def runscript():
    global events, counter, cond, prev_player_state, prev_quality
    counter += 1
    print 'Every second'
    # time.sleep(1)

    stats = driver.execute_script('''
    getPlayer = function() {
    const videoPlayer = netflix.appContext.state.playerApp.getAPI().videoPlayer;

    const playerSessionId = videoPlayer.getAllPlayerSessionIds()[0];

    const player = videoPlayer.getVideoPlayerBySessionId(playerSessionId);
                        
    return player;
};
    var nfx_player = getPlayer();
    info_now = nfx_player.diagnostics.getGroups();
    console.log(info_now);
    return info_now;
''')
    time_now = time.time()
    result = {}
    for item in stats:
        result.update(item)
    print result
    print '-------- ^^ resulst ^^ -----------'
    print 'throughput is ---- > ', result['Throughput']
    prev_download = 0
    try:
        with open('download_'+contentprovider+'_'+network+'.txt','a') as f:
            f.write( str(time_now)+','+str(result['Throughput'].replace(' kbps',''))+'\n')
            prev_download = result['Throughput'].replace(' kbps','')
    except Exception as exp:
        print str(exp)
        with open('download_'+contentprovider+'_'+network+'.txt','a') as f:
            f.write( str(time_now)+','+str(prev_download)+'\n')

    result['time'] = (int(time.time()*1000))
    quality = ''
    clean_d = {k.replace(' ', ''): v for k, v in result.items()}
    
    try:
        quality = re.findall(r'x.*',clean_d['Playingbitrate(a/v)'])[0].replace('x','').replace(')','').strip()
    except Exception as exp:
        print str(exp)
        pass
    print 'prev_quality ', prev_quality, ' quality ', quality

    if prev_quality != quality:
        prev_quality = quality
        print 'event being added ===========================================> quality changed'
        # prev_player_state = player_state
        result['changeevent'] = 'QualityChange'
        prev_player_state = 'QualityChange'
        events.append(result)
    else:
        player_state = clean_d['Renderingstate']
        result['changeevent'] = player_state

        print 'prev_player_state ', prev_player_state, ' player_state ', player_state
        print '=============='
        if prev_player_state == '':
            prev_player_state = player_state
            print 'event being added ========================================> previous state differs'
            prev_player_state = player_state
            result['changeevent'] = player_state
            events.append(result)

        else:
            # indicates player state change
            if prev_player_state != player_state:
                print 'event being added ============================================> previous state differs'
                prev_player_state = player_state
                result['changeevent'] = player_state
                events.append(result)

    # time.sleep(1)
    if counter == stoptime:
        cond = False
# first loaded player page

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print(timeformat)
        time.sleep(1)
        runscript()
        t -= 1
    print('Timer 0!\n')


result = {}
result['time'] = (int(time.time()*1000))
result['changeevent'] = 'Unstarted'
events.append(result)


countdown(stoptime)

stats = driver.execute_script('''
getPlayer = function() {
const videoPlayer = netflix.appContext.state.playerApp.getAPI().videoPlayer;

const playerSessionId = videoPlayer.getAllPlayerSessionIds()[0];

const player = videoPlayer.getVideoPlayerBySessionId(playerSessionId);
                    
return player;
};
var nfx_player = getPlayer();
nfx_player.pause();
info_now = nfx_player.diagnostics.getGroups();
console.log(info_now);
return info_now;
''')
time_now = time.time()
result = {}
for item in stats:
    result.update(item)
print result
print '-------- ^^ resulst ^^ -----------'
result['changeevent'] = 'Pause'
result['time'] = (int(time.time()*1000))
events.append(result)



print 'events are : '
print events
print '................................................'
results = {}
userID = random_ascii_by_size(10)
results['network'] = network
results['testID'] = testID
results['events'] = events
results['userID'] = userID
results['videoID'] = videoID
results['contentprovider'] = contentprovider
results['tether'] = tether

# r = requests.post("http://128.119.245.88:55556/", data=json.dumps(results))
r = requests.post("http://localhost:55556/", data=json.dumps(results))

# analyzer = analyzerI('128.119.245.88',55556)
analyzer = analyzerI('localhost',55556)
results = analyzer.getSingleResult(userID)
results = results['response']

print results
print '\r\n Summary:'

print '\t & '.join(
    ['videoID', 'initialQuality', 'endQuality', 'timeInDiffQualities', 'timeToStartPlaying', 'qualityChangeCount', 'rebufferCount',
     'finalFractionLoaded', 'bufferingTimeFrac', 'bufferingTime', 'playingTime'])

# results is keyed by videoID
for q in sorted(results.keys()):
    iQualities = getQualityPercentage(results[q]['initialQuality'])
    eQualities = getQualityPercentage(results[q]['endQuality'])
    dQualities = getQualityPeriod(results[q]['multiTestsQualities'])

    print '\t & '.join(map(str, [q, iQualities, eQualities, dQualities,
                             round(numpy.average(results[q]['timeToStartPlaying'])/1000.0, 2),
                             round(numpy.average(results[q]['qualityChangeCount']), 2),
                             round(numpy.average(results[q]['rebufferCount']), 2),
                             str(round(numpy.average(results[q]['finalFractionLoaded']), 2) * 100) + '%',
                             str(round(numpy.average(results[q]['bufferingTimeFrac']), 2)) + '%',
                             round(numpy.average(results[q]['bufferingTime']), 2),
                             round(numpy.average(results[q]['playingTime']), 2)
                             ]))

    print '\r\n All quality change and buffering events ', results[q]['bEvents'], '\r\n'
    if doGraphs:
        currdir = os.getcwd()
        dirName = currdir + '/graphs/' + userID + '/'
        # make directory for
        if not os.path.isdir(dirName):
            os.makedirs(dirName)
        graphTitle = '{}_{}_{}_{}'.format(network, tether, browser, q)
        count = 0

        for bevents in results[q]['bEvents']:
            filename = dirName + graphTitle + '_' + str(count) + '.png'
            with open(str(filename.replace('.png','.txt')), 'wb') as f:
                pickle.dump(bevents, f)

            drawQualityChangeGraph(bevents, float(stoptime), filename)
            count += 1

driver.quit()