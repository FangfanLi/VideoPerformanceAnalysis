from xml.dom import minidom
import glob
import re
import matplotlib.pyplot as plt

bandwidths = []
times = []
# parse an xml file by name
prev_time = 0
xml_files = glob.glob('/Users/arian/Desktop/XML/*.xml')
print xml_files
xml_files.sort(key=lambda f: int(filter(str.isdigit, f)))
print xml_files
print '--------------------'
for xml in xml_files:
    print xml
    time = xml.split('_')[1].replace('.xml','')
    if prev_time == 0:
    	prev_time = time
    	
    times.append(float(time)-float(prev_time))

    mydoc = minidom.parse(xml)
    items = mydoc.getElementsByTagName('node')
    for elem in items:
	txt = (elem.attributes['text'].value)
	if txt != "":
	    # print txt
	    bandwidth_mbps = re.findall(r'.*mbps', txt)
	    bandwidth_kbps = re.findall(r'.*kbps', txt)
	    if len(bandwidth_mbps) > 0:
	    	bandwidth_mbps = float(bandwidth_mbps[0].replace(' ','').replace('mbps',''))
	    	bandwidths.append(bandwidth_mbps*1000)
	    	print bandwidth_mbps*1000
	    if len(bandwidth_kbps) > 0:
	    	print bandwidth_kbps[0].replace(' ','').replace('kbps','')
	    	bandwidths.append(bandwidth_kbps[0].replace(' ','').replace('kbps',''))
	    # print bandwidth_kbps, bandwidth_mbps
    print '------------'

plt.plot(times, bandwidths, label='TMobile')
plt.legend()
plt.xlabel('Time (s)')
plt.ylabel('Bandwidth/Download Speed Kbps')
plt.title('Download Speed of TMobile on the phone app')
plt.show()
print times
print bandwidths