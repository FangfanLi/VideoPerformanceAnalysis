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
	N = 10
	list_of_tuples = []
	list_of_tuples_labels = []
	resolutions = ['240p','360p','480p','720p','1080p']
	tuple_240p = ()
	tuple_360p = ()
	tuple_480p = ()
	tuple_720p = ()
	tuple_1080p = ()
	tuples = [tuple_240p, tuple_360p,tuple_480p,tuple_720p,tuple_1080p]


	if len(json_file) !=1:
		with open(json_file, 'r') as fp:
			histogram_data = json.load(fp)
	else:
		histogram_data = {
			'bevents_ATT_youtube': {'360p': 4.9, '240p': 0.1},
			'bevents_Sprint_youtube': {'480p': 4.558333333333334, '360p': 0.425, '240p': 0.016666666666666666}, 
			'bevents_TMobile_youtube': {'480p': 2.7, '360p': 2.3}, 
			'bevents_Verizon_youtube': {'480p': 3.208333333333333, '360p': 1.7916666666666667}, 
			'bevents_ATT_VPN_ATT': {'480p': 0.08333333333333333, '360p': 0.33333333333333337, '720p': 4.583333333333333},
			'bevents_Sprint_VPN_Sprint': {'480p': 0.10833333333333334, '360p': 0.32499999999999996, '720p': 4.566666666666666}, 
			'bevents_TMobile_VPN_TMobile': {'360p': 0.41666666666666663, '720p': 4.583333333333333},   
			'bevents_Verizon_VPN_Verizon': {'360p': 0.41666666666666663, '720p': 4.583333333333333}, 
			'bevents_WiFi_youtube': {'480p': 0.20833333333333331, '360p': 0.25, '720p': 4.541666666666667},
			'bevents_WiFi_VPN_WiFi': {'360p': 0.32499999999999996, '720p': 4.675}
		}




	for entry in list(histogram_data.keys())[0:10]:
		cnt = 0
		print(entry,histogram_data[entry], ' entry -- ')
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
			list_of_tuples_labels.append(entry.split('_')[1]+" VPN")
		else:
			list_of_tuples_labels.append(entry.split('_')[1])
			
	print(tuples)
	print(list_of_tuples_labels)




	ind = np.arange(N)    # the x locations for the groups
	ind = [0,0.5,1,1.5,2,2.5,3,3.5,4,4.5]
	width = 0.20       # the width of the bars: can also be len(x) sequence

	p1 = plt.bar(ind, tuples[0], width,color='#2171b5', label ='LD',edgecolor='black')
	p2 = plt.bar(ind, tuples[1], width,color='#6baed6',label='SD low',edgecolor='black',
	             bottom=tuples[0])
	p3 = plt.bar(ind, tuples[2], width, color='#bdd7e7',label='SD',edgecolor='black',
	             bottom=tuple(map(sum,zip(tuples[0],tuples[1]))))
	p4 = plt.bar(ind, tuples[3], width, color='#eff3ff',label='HD',edgecolor='black',
	             bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2]))))

	p5 = plt.bar(ind, tuples[4], width, color='orchid',
	             bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3]))))

	plt.ylabel('Percentage of Time')
	# plt.axvline(x=3.5,color='black',linestyle='--')
	# plt.axvline(x=3.5,color='black')
	# plt.axvline(x=7.52058956,color='black')
	# plt.axvline(x=7.5, color='black',linestyle='--')
	plt.xticks(ind, ('ATT','Sprint','TMobile','Verizon','ATT','Sprint','TMobile','Verizon','WiFi','WiFi\nVPN'))
	plt.yticks(np.arange(0, 110, 20))
	# plt.legend((p1[0], p2[0],p3[0],p4[0],p5[0]), (resolutions[0], resolutions[1], resolutions[2],resolutions[3],resolutions[4]))
	
	plt.annotate('Exposed',
            xy=(150, 280), xycoords='figure pixels')

	plt.annotate('VPN',
            xy=(430, 280), xycoords='figure pixels')

	plt.annotate('WiFi',
            xy=(600, 280), xycoords='figure pixels')

	plt.legend(bbox_to_anchor=(0,1.12,1,0.2),mode="expand" , ncol=4, loc="lower left")
	plt.xticks(rotation=45,horizontalalignment="center")
	fig.tight_layout()

	plt.savefig('a.png',bbox_inches="tight")

	# plt.show()



def main():

    content_provider = 'Youtube'
    histogram_data = {}
    fig, ax = matplotlib.pyplot.subplots(figsize=(5.3, 3.8))

    try:
        json_file = sys.argv[1]
    except:
        print ('Please provide a JSON file')

    plt_his = plot_stacked(histogram_data,fig,ax,json_file)
    print('----------------------------')
    # plt_his.show()
if __name__ == "__main__":
    main()

