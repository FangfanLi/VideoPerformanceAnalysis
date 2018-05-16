import subprocess
import time

counter = 0
cond = True
global prev_time
prev_time = 0
def captureWindowdump():
    global prev_time
    global counter
    global cond
    counter += 1
    print counter
    time_now = time.time()
    if prev_time == 0:
        prev_time = time_now
    print (float(time_now) - float(prev_time))
    print "Every 5 second"
    test = subprocess.Popen(["adb","shell", "uiautomator","dump", "/sdcard/window_"+str(time_now).split('.')[0]+'.xml'], stdout=subprocess.PIPE)
    output = test.communicate()[0]
    print output
    print 'pull data'

    test = subprocess.Popen(["adb","pull","/sdcard/window_"+str(time_now).split('.')[0]+'.xml'], stdout=subprocess.PIPE)
    output = test.communicate()[0]
    print output
    # time.sleep(1)
    if ((float(time_now) - float(prev_time)) > 120):
        cond = False

while cond:
    captureWindowdump()

