import subprocess
import time

counter = 0
cond = True
def captureScreenshot():
	global counter
	global cond
	counter += 1
	time_now = time.time()
	print "Every 1 seconds"
        test = subprocess.Popen(["adb","shell", "screencap","-p", "/sdcard/capture_"+str(time_now).split('.')[0]+'.png'], stdout=subprocess.PIPE)
	output = test.communicate()[0]
	print output
	print 'pull data'

	test = subprocess.Popen(["adb","pull","/sdcard/capture_"+str(time_now).split('.')[0]+'.png'], stdout=subprocess.PIPE)
	output = test.communicate()[0]
	print output
	time.sleep(1)
	if counter == 30:
	    cond = False

while cond:
    captureScreenshot()






