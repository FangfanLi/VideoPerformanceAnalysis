# -*- coding: utf-8 -*-
'''

This script tests Youtube performance by repeatedly

Few parameters that can be modified:

videoIDs can be replaced with the output of calling getTopYoutubeVideoIDs(n)

doDumps default False, when set to True, will record pcap traces while running each experiment

stoptime default 10, how many seconds the video plays

rounds default 5, how many rounds of test to perform for each video

Inputs are 1. the network being tested 2. Whether you are tethered 3. The browser used for testing  4. The video streaming serivce
Example usage:
    python automated_youtube_api.py [Network] [YES or NO] [Chrome OR Firefox] [youtube or vimeo]
'''

import time, sys, os, random, string, subprocess, urllib2, json, urllib, numpy
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup
import matplotlib.pyplot as plt
from selenium.webdriver.common.keys import Keys

from io import BytesIO
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import subprocess
import re
import pickle


'''
Get the video IDs of the top n Youtube videos from Wikipedia
The wikipedia page keeps track of the top 100 most viewed Youtube videos

Input : n
Output : a list of n most viewed Youtube video IDs 
'''

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

def drawQualityChangeGraph(bevents, endtime, filename, contentprovider):
    fig, ax = plt.subplots()
    plt.ylim((0, 7.5))

    plt.xlim((0, endtime))
    if contentprovider == 'youtube':
        quality2y = {'tiny': 1, 'small': 2, 'medium': 3, 'large': 4, 'hd720': 5, 'hd1080': 6, 'hd1440':7}
    if contentprovider == 'vimeo':
        quality2y = {'270p': 1, '360p': 2, '540p': 3, '720p': 4, '1080p': 5, '2K': 6, '4K': 7}

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
        print bufferingLine
        x1x2 = bufferingLine[0]
        y1y2 = bufferingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='r', linewidth=3)

    for playingLine in playingLines:
        x1x2 = playingLine[0]
        y1y2 = playingLine[1]
        plt.plot(x1x2, y1y2, 'k-', color='b')
    if contentprovider == 'youtube':
        ax.set_yticklabels(['', 'tiny', 'small', 'medium', 'large', '720P', '1080P','1440'])
    if contentprovider == 'vimeo':
        ax.set_yticklabels(['', '270p', '360p', '540p', '720p', '1080p', '2K', '4K'])

    plt.title((filename).split('/')[-1])

    plt.savefig(filename + '.png')

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

def getTopYoutubeVideoIDs(n):
    if n > 100:
        n = 100
    url = 'https://en.wikipedia.org/wiki/List_of_most-viewed_YouTube_videos'
    soup = BeautifulSoup(urlopen(url).read())

    sortTable = soup.find("table", {"class": "wikitable sortable"})

    refTable = soup.find("div", {"class": "reflist columns references-column-width"})
    allVideo = sortTable.findAll("tr")

    allIDs = []

    for ind in xrange(1, n+1):
        video = allVideo[ind]
        td = video.findAll("td")[1]
        # print '\r\n td', td
        refID = td.find('sup').find('a').get('href').split('#')[1]
        # print '\r\n refID',refID
        allIDs.append(refID)

    allYoutubeIDs = []
    for ref in refTable.findAll("li"):
        # print '\r\n ~',ref.get('id'), ref.get('id') == refID
        if ref.get('id') in allIDs:
            link = ref.find('a', {"class": "external text"}).get('href')
            youtubeID = link.split('=')[1]
            allYoutubeIDs.append(youtubeID)

    return allYoutubeIDs


def random_ascii_by_size(size):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))

def runOne(tether, stoptime, network, quality, contentprovider ,videoID=None,driver=None, userID=None, testID=None, doDumps=False):
    # url = 'http://www.ccs.neu.edu/home/fangfanli/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}'.format(tether, stoptime, network, quality,videoID)
    # url = 'http://oban.cs.umass.edu/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}&contentprovider={}'.format(tether, stoptime, network, quality,videoID,contentprovider)
    url = 'http://localhost/~arian/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}&contentprovider={}'.format(tether, stoptime, network, quality,videoID,contentprovider)
    if userID:
        url += '&userID=' + userID
    if testID:
        url += '&testID=' + str(testID)

    # If doDumps = True, record the traces when testing
    if doDumps:
        currdir = os.getcwd()
        dirName = currdir + '/tcpdumps/' + userID + '/'
        # make directory for
        if not os.path.isdir(dirName):
            os.makedirs(dirName)
        dumpName = 'dump_youtubeAPI_{}_{}_{}_{}.pcap'.format(userID, network, videoID, testID)
        command  = ['sudo','tcpdump', '-nn', '-B', str(131072), '-w', dirName + dumpName]
        pID      = subprocess.Popen(command)

    driver.get(url)

    driver.find_element_by_id('player').click()

    # The next two lines opens a right click drop down menu, which contains option 'stats for nerds'
    actionChains = ActionChains(driver)
    actionChains.move_to_element(driver.find_element_by_id('player')).context_click().perform()
    # Need to then select 'stats for nerds' element, selecting element from a drop down menu is not super straight forward though

    prev_download = 0

    while True:
        status = driver.execute_script("return localStorage.getItem('status');")
        if status == 'done':
            break
        # time.sleep(1)
        element = driver.find_element_by_id('player') # find part of the page you want image of
        location = element.location
        size = element.size

        png = driver.get_screenshot_as_png()
        im = Image.open(BytesIO(png)) # uses PIL library to open image in memory

        time_now = (int(time.time()*1000))
        filename = str(time_now)+'.png'
        im = im.crop((300, 200, 1100, 700)) # defines crop points
        im.save('screenshots_youtube/'+filename) # saves new cropped image
        # image = cv2.imread('screenshots_vimeo/'+filename)
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # gray = cv2.medianBlur(gray, 3)
        # cv2.imwrite('screenshots_vimeo/pre_'+filename,gray)
        # os.remove('screenshots_vimeo/'+filename)
        Image.open('screenshots_youtube/'+filename)

        test = subprocess.Popen(["tesseract","-l","eng",'screenshots_youtube/'+filename, 'stdout'], stdout=subprocess.PIPE)
        
        output = test.communicate()[0]
        print output
        print '.........'
        download = re.findall(r'.*Kb',output)
        print download , ' this is the download info '
        try:
            if len(download[0]) < 6:
                download[0] = prev_download
            with open('download_'+contentprovider+'_'+network + '_' + tether + '.txt','a') as f:
                f.write( str(int(time.time()))+','+str(download[0].split('Kb')[0].replace(' ',''))+'\n')
            prev_download = str(download[0].split('Kb')[0].replace(' ',''))
        except Exception as exp:
            print str(exp)
            with open('download_'+contentprovider+'_'+network + '_' + tether + '.txt','a') as f:
                f.write( str(int(time.time()))+','+str(prev_download)+'\n')
            pass

    if doDumps:
        pID.terminate()
        
    driver.close()


def runOneV(tether, stoptime, network, quality, contentprovider ,videoID=None,driver=None, userID=None, testID=None, doDumps=False):
    # url = 'http://www.ccs.neu.edu/home/fangfanli/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}'.format(tether, stoptime, network, quality,videoID)
    # url = 'http://oban.cs.umass.edu/vimeoPlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}&contentprovider={}'.format(tether, stoptime, network, quality,videoID,contentprovider)
    url = 'http://localhost/~arian/vimeoPlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}&contentprovider={}'.format(tether, stoptime, network, quality,videoID,contentprovider)

    if userID:
        url += '&userID=' + userID
    if testID:
        url += '&testID=' + str(testID)

    # If doDumps = True, record the traces when testing
    if doDumps:
        currdir = os.getcwd()
        dirName = currdir + '/tcpdumps/' + userID + '/'
        # make directory for
        if not os.path.isdir(dirName):
            os.makedirs(dirName)
        dumpName = 'dump_vimeoAPI_{}_{}_{}_{}.pcap'.format(userID, network, videoID, testID)
        command  = ['sudo','tcpdump', '-nn', '-B', str(131072), '-w', dirName + dumpName]
        pID      = subprocess.Popen(command)
# 
    driver.get(url)
    # The next two lines opens a right click drop down menu, which contains option 'stats for nerds'
    # actionChains = ActionChains(driver)
    # actionChains.move_to_element(driver.find_element_by_id('player')).context_click().perform()
    # Need to then select 'stats for nerds' element, selecting element from a drop down menu is not super straight forward though
    run_once = 0
    quality_prev = ''
    prev_download = 0

    while True:
        status = driver.execute_script("return localStorage.getItem('status');")
        if status == 'done':
            break
        if run_once == 0:
            time.sleep(1)
            driver.find_element_by_id('playerid').click()
            # driver.find_element_by_id('playerid').click()
            actions = ActionChains(driver)
            actions.send_keys('d')
            actions.perform()
            print 'pressed D'
            print (int(time.time()*1000))
            run_once = 1
        element = driver.find_element_by_id('playerid') # find part of the page you want image of
        location = element.location
        size = element.size

        png = driver.get_screenshot_as_png()
        im = Image.open(BytesIO(png)) # uses PIL library to open image in memory

        time_now = (int(time.time()*1000))
        filename = str(time_now)+'.png'
        im = im.crop((0, 0, 500, 600)) # defines crop points
        im.save('screenshots_vimeo/'+filename) # saves new cropped image
        # image = cv2.imread('screenshots_vimeo/'+filename)
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        # gray = cv2.medianBlur(gray, 3)
        # cv2.imwrite('screenshots_vimeo/pre_'+filename,gray)
        # os.remove('screenshots_vimeo/'+filename)
        Image.open('screenshots_vimeo/'+filename)

        test = subprocess.Popen(["tesseract","-l","eng",'screenshots_vimeo/'+filename, 'stdout'], stdout=subprocess.PIPE)
        
        output = test.communicate()[0]
        # print output
        print '.........'
        download = re.findall(r'Bandwidth.*Kbps',output)
        print download , ' this is the download info '
        try:
            with open('download_'+contentprovider+'_'+network+ '_' + tether+'.txt','a') as f:
                f.write( str(int(time.time()))+','+str(download[0].split('Bandwidth: ')[1].split('Kbps')[0].replace(',','')).replace(' ','')+'\n')
            prev_download = (download[0].split('Bandwidth: ')[1].split('Kbps')[0].replace(',','').replace(' ',''))
            print 'this is Kbps , ', prev_download
        except Exception as exp:
            print str(exp)
            with open('download_'+contentprovider+'_'+network+ '_' + tether +'.txt','a') as f:
                f.write( str(int(time.time()))+','+str(prev_download)+'\n')
            pass
        a = re.findall(r'Profile .*',output)
        quality_now = ''
        try:
            quality_now = re.findall(r',.*',a[0])[0].replace(',','').strip()
            quality_now = quality_now.replace('120','720')
            quality_now = quality_now.replace('Ml','540')
            quality_now = quality_now.replace('1030','1080')
            quality_now = quality_now.replace('asap','540')
        except:
            pass
        print 'this is quality now ', str(quality_now), ' prev quality ', str(quality_prev)
        if (quality_prev) == '' and len(quality_now) > 1:
            script = "localStorage.setItem('prev_quality',\""+str(quality_now)+"\");"
            print script
            driver.execute_script("localStorage.setItem('init_quality',\""+str(quality_now)+"\");")
            driver.execute_script(script)
            driver.execute_script("localStorage.setItem('quality',\""+str(quality_now)+"\");")
            quality_prev = quality_now
            print 'quality now updated to  ' , quality_now
            print '==========================='
        elif len(quality_now) > 1:
            print 'we had some quality before ' 
            script = "localStorage.setItem('quality',\""+str(quality_now)+"\");"
            quality_prev = quality_now
            driver.execute_script(script)

        # os.remove('screenshots_vimeo/screenshot_'+str(time_now)+'.png')
    

    if doDumps:
        pID.terminate()

    # driver.close()


def main():
    try:
        network  = sys.argv[1]
        tether = sys.argv[2]
        browser = sys.argv[3]
        contentprovider = sys.argv[4]
    except:
        print '\r\n Please provide two inputs : [the network being tested (e.g. WiFi?)] [are you tethered (YES or NO)] [which browser to use (Firefox or Chrome)]'
        sys.exit(-1)
    # qualities = ["hd2160", "hd1440", "hd1080", "hd720", "large", "medium", "small", "tiny", "auto"]
    quality = 'auto'

    # This list contains the videoIDs to be tested, can be replaced with the top 50 list

    videoIDs = getTopYoutubeVideoIDs(1)
    # unique for a set of tests
    userID = random_ascii_by_size(10)

    # Whether do tcpdump
    doDumps = False
    # Wether draw event graph for each test
    doGraphs = True
    # Running time for each video
    stoptime = 120
    # Rounds of test for each video
    rounds = 1

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

    # runOne(name, stoptime, network, 'auto', driver=driver, userID=userID, testID=testID, doDumps=doDumps)

    for i in range(rounds):
        for videoID in videoIDs:
            testID = str(i)
            print '\t'.join(map(str, [testID, quality, contentprovider, network, browser, userID, videoID]))
            if contentprovider == 'youtube':
                videoID = 'bmGsQkLb4yg'
                # videoID = '635PgSuj_Ps'
                runOne(tether, stoptime, network, quality, contentprovider, videoID=videoID, driver=driver, userID=userID, testID=testID, doDumps=doDumps)
                # time.sleep(3)
            elif contentprovider == 'vimeo':
                # videoID = 262617592
                # videoID = 261363083
                videoID = 139874888
                runOneV(tether, stoptime, network, quality, contentprovider, videoID=videoID, driver=driver, userID=userID, testID=testID, doDumps=doDumps)
                # time.sleep(3)

    # if driver:
        # driver.quit()
    # analyzerI
    # analyzer = analyzerI('128.119.245.88',55556)
    analyzer = analyzerI('localhost',55556)
    results = analyzer.getSingleResult(userID)
    results = results['response']

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
                filename = dirName + graphTitle + '_' + contentprovider + '_'+ str(count) + '.png'
                with open(str(filename.replace('.png','.txt')), 'wb') as f:
                    pickle.dump(bevents, f)
                drawQualityChangeGraph(bevents, float(stoptime), filename, contentprovider)
                count += 1


if __name__ == "__main__":
    main()