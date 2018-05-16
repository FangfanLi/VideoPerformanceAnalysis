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
from selenium.webdriver.common.by import By

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains


try:
    network  = sys.argv[1]
    tether = sys.argv[2]
    browser = sys.argv[3]
    testID = sys.argv[4]
    videoID = sys.argv[5]
    contentprovider = sys.argv[6]
except:
    print '\r\n Please provide two inputs : [the network being tested (e.g. WiFi?)] [are you tethered (YES or NO)] [which browser to use (Firefox or Chrome)]'
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
    print bevents
    print '------------'
    fig, ax = plt.subplots()
    plt.ylim((0, 7))

    plt.xlim((0, endtime))
    plt.xlabel('Time')
    plt.ylabel('Video Quality')
    quality2y = {'240': 1, '360': 2, '480': 3, '720': 4, '1080': 5, '1440': 6}

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
            print 'timeStamp'
            print timeStamp
            print 'ntimeStamp'
            print ntimeStamp
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
        plt.plot(x1x2, y1y2, 'k-', color='r', linewidth=3)

    for playingLine in playingLines:
        x1x2 = playingLine[0]
        y1y2 = playingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='b')

    ax.set_yticklabels(['', '240', '360', '480', '720', '1080', '1440'])

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
driver.get("https://www.amazon.com/ap/signin?_encoding=UTF8&ignoreAuthState=1&openid.assoc_handle=usflex&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2Fgp%2Fvideo%2Fdetail%2FB01MDTS4VZ%2Fref%3Dnav_signin%3Fie%3DUTF8%26pf_rd_i%3Dhome%26pf_rd_m%3DATVPDKIKX0DER%26pf_rd_p%3D3194252682%26pf_rd_r%3DH3FH1NHR79DWAF0XTWD2%26pf_rd_s%3Dcenter-4%26pf_rd_t%3D12401&switch_account=")
# login = driver.find_element_by_css_selector(".authLinks.signupBasicHeader")
# login.click()
element = driver.find_element_by_id("ap_email")
element.send_keys("arian@cs.umass.edu")
# element.send_keys("arianniaki@gmail.com")
element2 = driver.find_element_by_id("ap_password")
element2.send_keys("Amazon123456m.donthackme@")
submit = driver.find_element_by_id("signInSubmit")
submit.click()

# submit2 = driver.find_element_by_css_selector(".btn.login-button.btn-submit.btn-small")
# print 'waited'
# submit2.click()
# # open the play page
driver.get("https://www.amazon.com/gp/video/detail/B01MDTS4VZ/ref=nav_signin?ie=UTF8&pf_rd_i=home&pf_rd_m=ATVPDKIKX0DER&pf_rd_p=3194252682&pf_rd_r=H3FH1NHR79DWAF0XTWD2&pf_rd_s=center-4&pf_rd_t=12401&")
# submit = driver.find_element_by_id("dv-buybox-play")
submit = driver.find_element_by_link_text("Continue Watching")
submit.click()
print submit




# elementList = submit.find_element_by_class("dv-play-btn deeplinkable")

# elementList.click()

# driver.execute_script("console.log('wow');")

# print 'bye'
counter = 0
cond = True
events = []
stoptime = 120
prev_player_state = ''
prev_quality = ''

flag_1080 = 0


def runscript():
    global events, counter, cond, prev_player_state, prev_quality, flag_1080
    counter += 1
    print 'Every second'
    # time.sleep(1)
    player_state = 'Unstarted'
    quality = ''
    try:
        web = driver.find_element(By.XPATH, "//div[@class='hdIndicator']")
        try:
            web1080 = driver.find_element(By.XPATH, "//div[@class='hd1080p']")
            flag_1080 = 1
            quality = '1080'
            print '1080HD'

        except Exception as exp:
            flag_1080 = 0
            pass
        img = driver.find_element(By.XPATH, "//div[@class='hdIndicator']//img[@class='svgBackground']")

        print '>>>>>>'
        # print img.get_attribute('src')
        if img.get_attribute('src') == "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzNi44NTkiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgLTMgMzYuODU5IDIwIj48ZyBmaWxsPSIjRkZGIj48cGF0aCBkPSJNMTYgMTdWLTNoLTR2OEg0di04SDB2MjBoNFY5aDh2OGg0ek0yNy42MjUgMTdjMi45MzggMCA1LjIwMy0uODc1IDYuODI4LTIuNjI1IDEuNjEtMS43NSAyLjQyMi00LjIyIDIuNDIyLTcuNDM4cy0uODEyLTUuNjEtMi40MjItNy4zNDRDMzIuODI4LTIuMTI1IDMwLjUzLTMgMjcuNTQ3LTNIMjB2MjBoNy42MjV6bS0uODktMTdDMzAuMjM0IDAgMzMgMi4zOSAzMyA2LjY0di45NTRDMzMgMTEuODc0IDMwLjI1IDE0IDI2Ljc1IDE0SDI0VjBoMi43MzR6Ii8+PC9nPjwvc3ZnPg==":
            if flag_1080 == 0:
            # print 'HD'
                quality = '720'
        elif img.get_attribute('src') == 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzNi44NTkiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgLTMgMzYuODU5IDIwIj48ZyBvcGFjaXR5PSIuMjUiIGZpbGw9IiNmZmYiPjxwYXRoIGQ9Ik0xNiAxN1YtM2gtNHY4SDR2LThIMHYyMGg0VjloOHY4aDR6TTI3LjYyNSAxN2MyLjkzOCAwIDUuMjAzLS44NzUgNi44MjgtMi42MjUgMS42MS0xLjc1IDIuNDIyLTQuMjIgMi40MjItNy40MzhzLS44MTItNS42MS0yLjQyMi03LjM0NEMzMi44MjgtMi4xMjUgMzAuNTMtMyAyNy41NDctM0gyMHYyMGg3LjYyNXptLS44OS0xN0MzMC4yMzQgMCAzMyAyLjM5IDMzIDYuNjR2Ljk1NEMzMyAxMS44NzQgMzAuMjUgMTQgMjYuNzUgMTRIMjRWMGgyLjczNHoiLz48L2c+PC9zdmc+':
            # print 'SD'
            quality = '480'
        else:
            # not HD SD is shown
            print '-------------------------------------------------------------- 360'
            quality = '360'
    except Exception as exp:
        pass  

    # This is because of a bug seeing a '' quality

    if quality == '':
        try:
            print img.get_attribute('src')
            print driver.find_element(By.XPATH, "//div[@class='hd1080p']")
        except Exception as exp:
            pass

        quality = prev_quality

    try:
        buffering = driver.find_element(By.XPATH, "//div[@class='overlay']//div[@class='loadingSpinner whiteSpinner']").get_attribute('style')
        if 'none' in buffering:
            player_state = 'Playing'
        if 'inline' in buffering:
            player_state = 'Buffering'
        print '----->'
        print player_state
        print '<-----'
    except Exception as exp:
        try:
            buffering = driver.find_element(By.XPATH, "//div[@class='loadingSpinner whiteSpinner']")[0].get_attribute('style')
            if 'none' in buffering:
                player_state = 'Playing'
            if 'inline' in buffering:
                player_state = 'Buffering'
            print '-- 1  --->'
            print player_state
            print '<--- 1 --'

        except Exception as exp:
            try:
                buffering = driver.find_element(By.XPATH, "//div[@class='loadingSpinner whiteSpinner']")[1].get_attribute('style')
                if 'none' in buffering:
                    player_state = 'Playing'
                if 'inline' in buffering:
                    player_state = 'Buffering'
                print '--- 2 -->'
                print player_state
                print '<-- 2---'

            except Exception as exp:
                pass



    stats = driver.execute_script('''
        const a  = window.ue_csm.localStorage;
        return a;
''')


    print 'PLAYER STATE is ' + str(player_state)
    time_now = time.time()
    print '-------- ^^ resulst ^^ -----------'
    result = {}
    try:
        result['Throughput'] = stats['last_bitrate_bps']
        network_bandwidth = stats['last_network_data']
        print '???????????'
        print network_bandwidth
        print '???????????'
    except Exception as exp:
        print str(exp)
        result['Throughput'] = 0
    print 'throughput is ---- > ', result['Throughput']
    prev_download = 0
    try:
        with open('download_'+contentprovider+'_'+network+'.txt','a') as f:
            f.write( str(time_now)+','+str(result['Throughput'])+'\n')
            prev_download = result['Throughput']
    except Exception as exp:
        print str(exp)
        with open('download_'+contentprovider+'_'+network+'.txt','a') as f:
            f.write( str(time_now)+','+str(prev_download)+'\n')

    result['time'] = (int(time.time()*1000))


    print 'prev_quality ', prev_quality, ' quality ', quality

    if prev_quality != quality:
        prev_quality = quality
        print 'event being added ===========================================> quality changed'
        # prev_player_state = player_state
        result['changeevent'] = 'QualityChange'
        result['quality'] = quality
        prev_player_state = 'QualityChange'
        events.append(result)
    else:
        # player_state = clean_d['Renderingstate']
        result['changeevent'] = player_state
        result['quality'] = quality

        print 'prev_player_state ', prev_player_state, ' player_state ', player_state
        print '=============='
        if prev_player_state == '':
            prev_player_state = player_state
            print 'event being added ========================================> previous state differs'
            prev_player_state = player_state
            result['changeevent'] = player_state
            result['quality'] = quality
            events.append(result)

        else:
            # indicates player state change
            if prev_player_state != player_state:
                print 'event being added ============================================ . .. . . . > previous state differs'
                prev_player_state = player_state
                result['changeevent'] = player_state
                result['quality'] = quality
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
        flag_1080 = 0
        runscript()
        ### 
        try:
            element_to_hover_over = driver.find_elements_by_xpath("//div[@class='pausedOverlay']")[0]
            hover = ActionChains(driver).move_to_element(element_to_hover_over)
            hover.perform()
            print ':::>>>'
        except Exception as exp:
            print '----------------------'

        t -= 1
    print('Goodbye!\n\n\n\n\n')


# uncommenting the below will cause the buffering event to start from second 1 rather than second 0
# print 'UNSTARTED EVENT' 
# result = {}
# result['time'] = (int(time.time()*1000))
# print 'start time ' + str(result['time'])
# result['quality'] = ''
# result['changeevent'] = 'Unstarted'
# events.append(result)
countdown(stoptime)


time_now = time.time()
result = {}

stats = driver.execute_script('''
    const a  = window.ue_csm.localStorage;
    return a;

''')

time_now = time.time()
print '-------- ^^ resulst ^^ -----------' + str(time_now)
result = {}
try:
    result['Throughput'] = stats['last_bitrate_bps']
except Exception as exp:
    print str(exp)
    result['Throughput'] = 0
print '-------- ^^ resulst ^^ -----------'
result['changeevent'] = 'Pause'
result['quality'] = prev_quality
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