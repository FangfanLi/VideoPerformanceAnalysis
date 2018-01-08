'''

This script tests Youtube performance by repeatedly

Few parameters that can be modified:

videoIDs can be replaced with the output of calling getTopYoutubeVideoIDs(n)

doDumps default False, when set to True, will record pcap traces while running each experiment

stoptime default 10, how many seconds the video plays

rounds default 5, how many rounds of test to perform for each video

Inputs are 1. the network being tested 2. Whether you are tethered 3. The browser used for testing
Example usage:
    python automated_youtube_api.py [Network] [YES or NO] [Chrome OR Firefox]
'''

import time, sys, os, random, string, subprocess
from selenium import webdriver
from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup


'''
Get the video IDs of the top n Youtube videos from Wikipedia
The wikipedia page keeps track of the top 100 most viewed Youtube videos

Input : n
Output : a list of n most viewed Youtube video IDs 
'''

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

def runOne(tether, stoptime, network, quality, videoID=None, driver=None, userID=None, testID=None, doDumps=False):

    url = 'http://www.ccs.neu.edu/home/fangfanli/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}'.format(tether, stoptime, network, quality,videoID)

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
    
    while True:
        status = driver.execute_script("return localStorage.getItem('status');")
        if status == 'done':
            break
        time.sleep(1)
    
    if doDumps:
        pID.terminate()



def main():
    try:
        network  = sys.argv[1]
        tether = sys.argv[2]
        browser = sys.argv[3]
    except:
        print '\r\n Please provide two inputs : [the network being tested (e.g. WiFi?)] [are you tethered (YES or NO)] [which browser to use (Firefox or Chrome)]'
        sys.exit(-1)
    # qualities = ["hd2160", "hd1440", "hd1080", "hd720", "large", "medium", "small", "tiny", "auto"]
    quality = 'auto'

    # This list contains the videoIDs to be tested, can be replaced with the top 50 list
    videoIDs = ['PsrPTpg6mNo', 'x1QTc5YeO6w']

    videoIDs = getTopYoutubeVideoIDs(2)

    # unique for a set of tests
    userID = random_ascii_by_size(10)

    # Whether do tcpdump
    doDumps = False
    # Running time for each video
    stoptime = '10'
    # Rounds of test for each video
    rounds = 5

    if browser == 'Chrome':
        userDir       = 'UserDir'
        chromeOptions = webdriver.ChromeOptions()
        options       = ['--user-data-dir={}'.format(userDir), '--disable-background-networking', '--disable-default-apps', '--disable-extensions']

        for o in options:
            chromeOptions.add_argument(o)
        driver = webdriver.Chrome('/Users/neufan/Downloads/chromedriver',chrome_options=chromeOptions)

    elif browser == 'Firefox':
        driver = webdriver.Firefox(executable_path='/Users/neufan/Downloads/geckodriver')
    else:
        print '\r\n Please specify a valid browser to us [Chrome OR Firefox]'
        sys.exit(-1)

    # runOne(name, stoptime, network, 'auto', driver=driver, userID=userID, testID=testID, doDumps=doDumps)

    for i in range(rounds):
        for videoID in videoIDs:
            testID = str(i)
            print '\t'.join(map(str, [testID, quality, network, userID, videoID]))
            runOne(tether, stoptime, network, quality, videoID=videoID, driver=driver, userID=userID, testID=testID, doDumps=doDumps)
            time.sleep(3)

    if driver:
        driver.quit()

if __name__ == "__main__":
    main()