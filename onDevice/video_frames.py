import cv2, time, glob, sys
import imutils

streaming_service  = sys.argv[1]
if streaming_service == "Youtube":
	files = glob.glob("Youtube/*.MP4")
else:
	files = glob.glob("Netflix/*.MOV")

rotate = sys.argv[2]
if rotate == 'rotate':
	rotate = 1
else:
	rotate = 0
for file in files:
	print file
	# print(cv2.__version__)
	vidcap = cv2.VideoCapture(file)
	success,image = vidcap.read()
	count = 0
	success = True
	while success:
	  if rotate == 1:
	  	image = imutils.rotate(image, 180)
	  cv2.imwrite("pictures/"+str(file.split('/')[1].split('_')[0])+"_"+str(file.split('/')[1].split('_')[1])+"_frame%d.jpg" % count, image)     # save frame as JPEG file
	  vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*1000))    # added this line 
	  success,image = vidcap.read()
	  print 'Read a new frame: ', success
	  count += 1
	  if count == 121: # after 2 minutes, break
	  	break