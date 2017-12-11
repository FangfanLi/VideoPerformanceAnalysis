'''
by: Arash Molavi Kakhki

Example:
    python automated_youtube_api_test.py Arash Tmobile-Home NA NA
'''

import time, sys, os, random, string, subprocess
from selenium import webdriver

def random_ascii_by_size(size):
    return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))

def runOne(name, tether, stoptime, network, quality, driver=None, userID=None, testID=None, doDumps=False):
    if not driver:

        userDir       = 'kirUserDir'
        chromeOptions = webdriver.ChromeOptions()
        options       = ['--user-data-dir={}'.format(userDir), '--disable-background-networking', '--disable-default-apps', '--disable-extensions']
        
        for o in options:
            chromeOptions.add_argument(o)
        
        # driver  = webdriver.Chrome(chrome_options=chromeOptions)
        exit    = True
        driver = webdriver.Chrome('/Users/neufan/Downloads/chromedriver',chrome_options=chromeOptions)
        # driver = webdriver.Chrome('/Users/neufan/Downloads/chromedriver')
    else:
        exit = False

    url = 'http://www.ccs.neu.edu/home/fangfanli/youtubePlayerStats.html?name={}&tether={}&stoptime={}&network={}&quality={}'.format(name, tether, stoptime, network, quality)
    # url     = 'http://achtung.ccs.neu.edu/~arash/youtubePlayerStats.html?name={}&stoptime={}&network={}&quality={}'.format(name, stoptime, network, quality)

    if userID:
        url += '&userID=' + userID
    if testID:
        url += '&testID=' + str(testID)
    
    
    if doDumps:
        dumpName = 'dump_youtubeAPI_{}_{}.pcap'.format(userID, testID) 
        command  = ['tcpdump', '-nn', '-B', str(131072), '-w', dumpName]
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
    
    if exit:
        os.system('rm -rf {}'.format(userDir))
        driver.quit()
    
name     = sys.argv[1]
network  = sys.argv[2]
tether = sys.argv[3]

# qualities = ["hd2160", "hd1440", "hd1080", "hd720", "large", "medium", "small", "tiny", "auto"]
qualities = ["hd1080", "hd720", "large", "medium", "small", "auto"]
# qualities = ["auto"]

# userDir       = 'kirUserDir'
# chromeOptions = webdriver.ChromeOptions()
# options       = ['--user-data-dir={}'.format(userDir), '--disable-background-networking', '--disable-default-apps', '--disable-extensions', '--disable-quic']
# driver        = webdriver.Chrome(chrome_options=chromeOptions)


userID = random_ascii_by_size(10)
testID = '0'

doDumps  = False
driver   = None
stoptime = '60'
rounds   = 5

# runOne(name, stoptime, network, 'auto', driver=driver, userID=userID, testID=testID, doDumps=doDumps)

for i in range(rounds):
    for quality in qualities:
        print '\t'.join( map(str, [i, quality, name, network, userID, testID]) )
        runOne(name, tether, stoptime, network, quality, driver=driver, userID=userID, testID=testID, doDumps=doDumps)
        testID = str(int(testID)+1)
        time.sleep(3)

if driver:
    driver.quit()
