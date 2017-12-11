'''
clear; adb kill-server; pkill -f chromedriver; adb devices; chromedriver

adb -s ZX1G22JSL7 shell getprop ro.product.model
adb -s ZX1G22JSL7 shell getprop ro.build.version.release
adb shell dumpsys netstats
adb shell dumpsys cpuinfo
adb shell dumpsys meminfo
adb shell dumpsys connectivity
'''

import sys, subprocess, time, os, json
from selenium import webdriver

def runADB():
    oldMotorola_deviceID = 'TA9650879H'
    nexus5_deviceID      = '09474a880ddf9720'
    nexus6_deviceID      = 'ZX1G22JSL7'
    
    p = subprocess.Popen(['adb', 'devices'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    print 'out:', out
    print 'err:', err
    if ('{}\tdevice'.format(nexus6_deviceID) in out) or ('{}\tdevice'.format(oldMotorola_deviceID) in out):
        print 'all good'
        return
    else:
        print '[a]Killing old server ...'
        output = subprocess.check_output(['adb', 'kill-server'])
        print '[b]Starting server ...'
        output = subprocess.check_output(['adb', 'start-server'])
        print '[c]Waiting for device ...'
        output = subprocess.check_output(['adb', 'wait-for-device'])
        print '[d]Listing devices ...'
        output = subprocess.check_output(['adb', 'devices'])
        print output
    
def runDriver():
#     output = subprocess.check_output(['pkill', '-f', 'chromedriver'])
    p = subprocess.Popen(['chromedriver'])
    time.sleep(2)
    return p
    
def getDriver(args=[]):
    
    capabilities = {'chromeOptions': {'androidPackage'  : 'com.android.chrome', 'args' : args}}
    
    gotDriver = False
    
    while not gotDriver:
        try:
            driver = webdriver.Remote('http://localhost:9515', capabilities)
            gotDriver = True
        except Exception as e:
            print '\EXCEPTOIOOOOOONNNNN!!!:', e
            print '.',; sys.stdout.flush()
            time.sleep(1)
    
    return driver

def initialize():
    PRINT_ACTION('Reading configs file and args)', 0)
    
    configs = Configs()
    
    configs.set('tcpdump'           , True)
    configs.set('networkInt'        , '')
    configs.set('rounds'            , 2)
    configs.set('mainDir'           , os.path.abspath('../data') + '/results')
    configs.set('appEnginePath'     , 'quic-project.appspot.com')
    configs.read_args(sys.argv)

    configs.check_for(['testDir', 'testPage'])

    configs.set('testDir', configs.get('mainDir') + '/' + configs.get('testDir') )
    
    configs.show_all()
    
    return configs

def main():
    
    url = 'http://achtung.ccs.neu.edu/~arash/testPage.html'
    
    runADB()
    runDriver()
    driver = getDriver()
    
    driver.get(url)
    events = driver.execute_script("return events;")
    for e in events:
        print e
    
    
    raw_input('\tPress enter to quit...\n')
    driver.quit()
        
if __name__=="__main__":
    main()
