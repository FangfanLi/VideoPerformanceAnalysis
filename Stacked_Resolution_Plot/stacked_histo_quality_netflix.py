import numpy as np
import matplotlib.pyplot as plt
import json
import subprocess, os, sys, numpy, random
import matplotlib.pyplot as plt
import glob
import matplotlib
from collections import OrderedDict
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from collections import namedtuple
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
matplotlib.rcParams.update({'font.size': 14})



def plot_stacked(histogram_data,fig,ax,json_file):
	N = 18
	list_of_tuples = []
	list_of_tuples_labels = []
	# resolutions = ['384x216','480x270','608x342','640x480','768x432','720x480','960x540','1280x720']
	resolutions = ['384x216','608x342','640x480','1280x720']
	tuple_384x216 = ()
	# tuple_480x270 = ()
	tuple_608x342 = ()
	tuple_640x480 = ()
	# tuple_768x432 = ()
	# tuple_720x480 = ()
	# tuple_960x540 = ()
	tuple_1280x720 = ()
	# tuple_1080 = ()
	# tuples = [tuple_384x216, tuple_480x270,tuple_608x342,tuple_640x480,tuple_768x432,tuple_720x480,tuple_960x540,tuple_1280x720]
	tuples = [tuple_384x216,tuple_608x342,tuple_640x480,tuple_1280x720]



	if len(json_file) !=1:
		with open(json_file, 'r') as fp:
			histogram_data = json.load(fp)
	else:
		histogram_data ={
		'bevents_ATT_Netflix': {'384x216': 5.0}, 
		'bevents_Sprint_Netflix': {'384x216': 5.0}, 
		'bevents_TMobile_Netflix': {'384x216': 5.0}, 
		'bevents_Verizon_Netflix': {'384x216': 5.0}, 

		'bevents_ATT_better_Netflix': {'480x270': 3.308333333333333, '384x216': 1.6916666666666667}, 
		'bevents_Sprint_better_Netflix': {'480x270': 2.9833333333333334, '384x216': 1.3250000000000002, '608x342': 0.6916666666666667}, 
		'bevents_TMobile_better_Netflix': {'480x270': 0.8416666666666666, '768x432': 0.5, '384x216': 2.1, '608x342': 1.5583333333333333}, 
		'bevents_Verizon_better_Netflix': {'480x270': 2.4166666666666665, '384x216': 1.9916666666666667, '608x342': 0.5916666666666667},    

		'bevents_ATT_VPN_Netflix': {'640x480': 5.0}, 
		'bevents_Sprint_VPN_Netflix': {'384x216': 5.0}, 
		'bevents_TMobile_VPN_Netflix': {'640x480': 5.0}, 
		'bevents_Verizon_VPN_Netflix': {'640x480': 5.0}, 

		'bevents_ATT_VPN_better_Netflix': {'1280x720': 3.875, '640x480': 0.08333333333333334, '720x480': 1.0416666666666667},
		'bevents_Sprint_VPN_better_Netflix': {'768x432': 0.47500000000000003, '608x342': 0.6583333333333333, '480x270': 0.6166666666666667, '384x216': 0.55, '960x540': 0.7083333333333334, '1280x720': 1.9916666666666667},
		'bevents_TMobile_VPN_better_Netflix': {'1280x720': 4.366666666666667, '640x480': 0.05, '720x480': 0.5833333333333333}, 
		'bevents_Verizon_VPN_better_Netflix': {'1280x720': 4.333333333333334, '640x480': 0.05, '720x480': 0.6166666666666667},

		'bevents_WiFi_Netflix': {'1280x720': 4.916666666666666, '720x480': 0.08333333333333333},
		'bevents_WiFi_VPN_Netflix': {'1280x720': 4.425, '640x480': 0.03333333333333333, '720x480': 0.5416666666666666}
		}




	for entry in list(histogram_data.keys())[0:18]:
		cnt = 0
		print(entry,histogram_data[entry])
		for i in resolutions:
			
			if i in histogram_data[entry].keys():
				print(i, cnt , histogram_data[entry][i])
				tuples[cnt] =tuples[cnt] + (float(histogram_data[entry][i]*100)/5,)
			else:
				print(i, cnt , 'no ')
				tuples[cnt] = tuples[cnt] + (float(0.0),)
			cnt += 1
		print(tuples)

		if entry.split('_')[2] == 'VPN':
			list_of_tuples_labels.append(entry.split('_')[1]+"VPN")
		else:
			list_of_tuples_labels.append(entry.split('_')[1])
			
	print(tuples)
	print(list_of_tuples_labels)



	ind = np.arange(N)    # the x locations for the groups
	width = 0.35       # the width of the bars: can also be len(x) sequence

	p1 = plt.bar(ind, tuples[0], width,color='#2171b5',label='LD',edgecolor='black',)
	p2 = plt.bar(ind, tuples[1], width,color='#6baed6',label='SD low',edgecolor='black',
	             bottom=tuples[0])
	p3 = plt.bar(ind, tuples[2], width, color='#bdd7e7',label='SD',edgecolor='black',
	             bottom=tuple(map(sum,zip(tuples[0],tuples[1]))))
	p4 = plt.bar(ind, tuples[3], width, color='#eff3ff',label='HD',edgecolor='black',
			bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2]))))
	# p1 = plt.bar(ind, tuples[0], width,color='#08306b',label='384x216',edgecolor='black',)
	# p2 = plt.bar(ind, tuples[1], width,color='#08519c',label='480x270',edgecolor='black',hatch="x",
	#              bottom=tuples[0])
	# p3 = plt.bar(ind, tuples[2], width, color='#2171b5',label='608x342',edgecolor='black',
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1]))))
	# p4 = plt.bar(ind, tuples[3], width, color='#4292c6',label='640x480',edgecolor='black',hatch="\\",
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2]))))
	# p5 = plt.bar(ind, tuples[4], width, color='#6baed6',label='768x432',edgecolor='black',
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3]))))
	# p6 = plt.bar(ind, tuples[5], width, color='#9ecae1',label='720x480',edgecolor='black',
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3],tuples[4]))))

	# p7 = plt.bar(ind, tuples[6], width, color='#c6dbef',label='960x540',edgecolor='black',hatch="+",
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3],tuples[4],tuples[5]))))
	# p8 = plt.bar(ind, tuples[7], width, color='#deebf7',label='1280x720',edgecolor='black', hatch="/",
	

	plt.ylabel('Percentage of Time')
	plt.axvline(x=3.5,color='black',linestyle='--')
	plt.axvline(x=7.5, color='black',linestyle='--')
	plt.axvline(x=11.5, color='black',linestyle='--')
	plt.axvline(x=15.5, color='black',linestyle='--')
	plt.xticks(ind, ('ATT','Sprint','TMobile','Verizon','ATT','Sprint','TMobile','Verizon','ATT','Sprint','TMobile','Verizon', 'ATT', 'Sprint','TMobile','Verizon','WiFi','WiFi VPN'))
	plt.yticks(np.arange(0, 110, 20))
	# plt.legend((p1[0], p2[0],p3[0],p4[0],p5[0]), (resolutions[0], resolutions[1], resolutions[2],resolutions[3],resolutions[4]))
	


	plt.legend(bbox_to_anchor=(0,1.12,1,0.2),mode="expand" , ncol=4, loc="lower left")
	plt.xticks(rotation=45,horizontalalignment="right")
	fig.tight_layout()
	plt.annotate('Exposed',
            xy=(120, 280), xycoords='figure pixels')

	plt.annotate('Max Data',
            xy=(260, 280), xycoords='figure pixels')

	plt.annotate('VPN',
            xy=(400, 280), xycoords='figure pixels')

	plt.annotate('VPN Max Data',
            xy=(480, 280), xycoords='figure pixels')

	plt.annotate('WiFi',
            xy=(630, 280), xycoords='figure pixels')

	plt.savefig('a.png',bbox_inches="tight")

	# plt.show()



def main():

    content_provider = 'Youtube'
    histogram_data = {}
    fig, ax = matplotlib.pyplot.subplots(figsize=(7.3, 3.8))
    try:
        json_file = sys.argv[1]
    except:
        print ('Please provide a JSON file')
  
    plt_his = plot_stacked(histogram_data,fig,ax,json_file)
    print('----------------------------')
    # plt_his.show()
if __name__ == "__main__":
    main()





