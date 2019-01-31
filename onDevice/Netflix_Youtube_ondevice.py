# coding: utf-8
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import subprocess
import glob
from os import system
# import the necessary packages
from PIL import Image
import pytesseract
import argparse
import cv2
import os
import imutils
import random, string, os, sys
import matplotlib.pyplot as plt


def random_ascii_by_size(size):
	return ''.join(random.choice(string.ascii_letters + string.digits) for x in range(size))


def drawQualityChangeGraph(bevents, endtime, filename):
	print '------------'
	fig, ax = plt.subplots()
	
	plt.ylim((0, 7))
	plt.xlim((0, endtime))
	plt.xlabel('Time')
	plt.ylabel('Video Quality')

	quality2y = {'':0, '144p':1, '240p':2, '360p':3 ,'480p': 4, '720p':5, '1080p':6}

	ticks = ['','144p','240p', '360p', '480p', '720p','1080p']

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




ap = argparse.ArgumentParser()
ap.add_argument("-p", "--preprocess", type=str, default="no",
	help="type of preprocessing to be done")
ap.add_argument("-s", "--streaming", type=str, default="Youtube",
	help="type the streaming services, Youtube or Netflix")
ap.add_argument("-r", "--rotate", type=int, default="0",
	help="rotate how many degrees")

ap.add_argument("-n", "--network", type=int, default="0",
	help="Enter the network being tested")


args = vars(ap.parse_args())

network  = args["network"]


resolutions = []
times = []

files = sorted(glob.glob('pictures/*.jpg'),key=os.path.getmtime) # sort files by mofigied date

for filename in (files):
	second = filename.split('e')[1]
	print '------------>',filename
	times.append(filename.split('/')[1].split('frame')[1].split('.jpg')[0])
	image = cv2.imread(filename)
	rotated = imutils.rotate_bound(image, args["rotate"])
	gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

	# check to see if we should apply thresholding to preprocess the
	# image
	if args["preprocess"] == "thresh":
		gray = cv2.threshold(gray, 0, 255,
			cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
		gray = cv2.medianBlur(gray, 3)
	# make a check to see if median blurring should be done to remove
	# noise
	elif args["preprocess"] == "blur":
		gray = cv2.medianBlur(gray, 3)
	 
	# write the grayscale image to disk as a temporary file so we can
	# apply OCR to it
	filename2 = "{}_.png".format(filename)
	cv2.imwrite(filename2, gray)


# 	# filename ='a.png'
# 	# img = Image.open(filename)
# 	# area = (0, 0, 800, 800)
# 	# cropped_img = img.crop(area)
# 	# cropped_img.show()
# 	# print filename
# 	# Image.open(filename)
# 	print 'image opened'

	
	# test = subprocess.Popen(["tesseract","-l","eng",filename2,'stdout','tessedit_char_whitelist=0123456789','-psm 6'], stdout=subprocess.PIPE)
	command = "tesseract "+ filename2+" stdout --psm 6 -c"
	print command

	output = subprocess.check_output(command, shell=True)
	# test = subprocess.Popen(["tesseract",filename2,'stdout','--psm 6','-c'], stdout=subprocess.PIPE)
	# output = test.communicate()[0]
	# os.remove(filename2)
	# print 'out:',filename2
	# print type(output)
	# print output

	output_lines = output.split('\n')
	print output_lines
	currQuality = ''
	found_flag = 0
	if args["streaming"] == "Youtube":
		print 'YOUTUBE'
		for line in output_lines:
			if '720' in str(line):
				resolutions.append('720p')
				currQuality = '720p'
				found_flag = 1
				break
			elif '360' in str(line):
				resolutions.append('360p')
				currQuality = '360p'
				found_flag =  1
			elif '369' in str(line):
				resolutions.append('360p')
				currQuality = '360p'
				found_flag = 1
			elif '60' in str(line):
				resolutions.append('360p')
				currQuality = '360p'
				found_flag = 1
			elif '134' in str(line):
				resolutions.append('360p')
				currQuality = '360p'
				found_flag = 1

			elif '359' in str(line):
				resolutions.append('360p')
				currQuality = '360p'
				found_flag = 1
				break
			elif '480' in str(line):
				resolutions.append('480p')
				currQuality = '480p'
				found_flag = 1
			elif '135' in str(line):
				resolutions.append('480p')
				currQuality = '480p'
				found_flag = 1
				break
			elif '240' in str(line):
				resolutions.append('240p')
				currQuality = '240p'
				found_flag = 1
			elif '133' in str(line):
				resolutions.append('240p')
				currQuality = '240p'
				found_flag = 1

				break
	if args["streaming"] == "Netflix":
		print 'Netflix'
		print output_lines
				# resolutions.append(resolutions[len(resolutions)-1])
			# else:
				# resolutions.append('')
	if found_flag == 0:
		print 'NOT ------------------------------------------------ FOUND'
		with open("not_found.txt","a") as f:
			f.write(filename+" "+currQuality +"\n")
	print resolutions
	print times

	# for netflix
	# if '84' in output:
	# 	if curr_quality == '':
	# 		bevents.append("Quality change : " + curr_quality + " : 0.0")
	# 		curr_quality = '384'
	# 	else:
	# 		bevents.append("Quality change : " + curr_quality + " : "+second)




bevents = ["Buffering : 0.0"]
bevents.append("Quality change : "+str(resolutions[0])+" : 0.0")
bevents.append("Playing : 0.0")

currQuality = resolutions[0]
for i in xrange(len(resolutions)):
	if currQuality != resolutions[i]:
		print resolutions[i], currQuality
		currQuality = resolutions[i]
		bevents.append("Quality change : "+str(resolutions[i])+" : "+str(times[i]))

# write bevents to file
with open("bevents_"+ str(network)+"_youtube.txt", 'w') as f:
	for item in bevents:
		f.write("%s\n" % item)



print bevents
endtime = 120
userID = random_ascii_by_size(10)
currdir = os.getcwd()
dirName = currdir + '/youtube_graphs/' + userID + '/'
if not os.path.isdir(dirName):
	os.makedirs(dirName)

graphTitle = '{}'.format(network)
filename = dirName + graphTitle + '_'  + '.png'
drawQualityChangeGraph(bevents, endtime, filename)