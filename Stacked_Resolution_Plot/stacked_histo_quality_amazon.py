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
	# resolutions = ['v5','v6','v7','v8','v9','v12']
	resolutions = ['v5','v8','v12']
	tuple_v5 = ()
	# tuple_v6 = ()
	# tuple_v7 = ()
	tuple_v8 = ()
	# tuple_v9 = ()
	tuple_v12 = ()
	# tuples = [tuple_v5,tuple_v6,tuple_v7,tuple_v8,tuple_v9,tuple_v12]
	tuples = [tuple_v5,tuple_v8,tuple_v12]


	if len(json_file) !=1:
		with open(json_file, 'r') as fp:
			histogram_data = json.load(fp)
	else:
		histogram_data ={
			'bevents_ATT_amazon': {'v8': 3.2916666666666665, 'v6': 0.26666666666666666, 'v7': 1.4416666666666667}, 
			'bevents_Sprint_amazon': {'v8': 3.4749999999999996, 'v5': 0.44999999999999996, 'v6': 0.125, 'v7': 0.95}, 
			'bevents_TMobile_amazon': {'v8': 2.816666666666667, 'v5': 0.058333333333333334, 'v6': 0.06666666666666667, 'v7': 2.0583333333333336}, 
			'bevents_Verizon_amazon': {'v8': 3.2916666666666665, 'v6': 0.1, 'v7': 1.6083333333333334},

			'bevents_ATT_better_amazon': {'v12': 3.8583333333333334, 'v9': 1.1416666666666666}, 
			'bevents_Sprint_better_amazon': {'v12': 3.9666666666666663, 'v9': 1.0333333333333332},
			'bevents_TMobile_better_amazon': {'v12': 3.975, 'v9': 1.025}, 	 
			'bevents_Verizon_better_amazon': {'v12': 3.6666666666666665, 'v9': 1.3333333333333335}, 

			'bevents_ATT_VPN_amazon': {'v8': 2.966666666666667, 'v7': 2.033333333333333},
			'bevents_Sprint_VPN_amazon': {'v8': 3.1083333333333334, 'v6': 0.03333333333333333, 'v7': 1.8583333333333334}, 
			'bevents_TMobile_VPN': {'v8': 2.841666666666667, 'v7': 2.158333333333333}, 
			'bevents_Verizon_VPN_amazon': {'v8': 2.85, 'v7': 2.15}, 

			'bevents_ATT_VPN_better_amazon': {'v12': 4.583333333333334, 'v9': 0.41666666666666663}, 
			'bevents_Sprint_VPN_better_amazon': {'v12': 4.425000000000001, 'v9': 0.5416666666666666, 'v8': 0.03333333333333333}, 
			'bevents_TMobile_VPN_better_amazon': {'v12': 4.625, 'v9': 0.375}, 
			'bevents_Verizon_VPN_better_amazon': {'v12': 4.533333333333333, 'v9': 0.4666666666666667},

			'bevents_WiFi_amazon': {'v12': 4.541666666666666, 'v9': 0.4083333333333333, 'v7': 0.05},
			'bevents_WiFi_VPN_amazon': {'v12': 4.625, 'v9': 0.375}
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
			list_of_tuples_labels.append(entry.split('_')[1]+" VPN")
		else:
			list_of_tuples_labels.append(entry.split('_')[1])
			
	print(tuples)
	print(list_of_tuples_labels)



	ind = np.arange(N)    # the x locations for the groups
	width = 0.35       # the width of the bars: can also be len(x) sequence

	p1 = plt.bar(ind, tuples[0], width,color='#2171b5',label='LD',edgecolor='black',)
	p2 = plt.bar(ind, tuples[1], width,color='#6baed6',label='SD low',edgecolor='black',
	             bottom=tuples[0])
	p3 = plt.bar(ind, tuples[2], width, color='#eff3ff',label='HD',edgecolor='black',
	             bottom=tuple(map(sum,zip(tuples[0],tuples[1]))))
	# p4 = plt.bar(ind, tuples[3], width, color='#6baed6',label='SD low',edgecolor='black',
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2]))))
	# p5 = plt.bar(ind, tuples[4], width, color='#9ecae1',label='HD',edgecolor='black',hatch="+",
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3]))))
	# p6 = plt.bar(ind, tuples[5], width, color='#c6dbef',label='HD',edgecolor='black',hatch="/",
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3],tuples[4]))))


	# p1 = plt.bar(ind, tuples[0], width,color='#084594',label='512x213',edgecolor='black',)
	# p2 = plt.bar(ind, tuples[1], width,color='#2171b5',label='652x272',edgecolor='black',hatch="x",
	#              bottom=tuples[0])
	# p3 = plt.bar(ind, tuples[2], width, color='#4292c6',label='710x296',edgecolor='black',
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1]))))
	# p4 = plt.bar(ind, tuples[3], width, color='#6baed6',label='710x296',edgecolor='black',
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2]))))
	# p5 = plt.bar(ind, tuples[4], width, color='#9ecae1',label='1152x480',edgecolor='black',hatch="+",
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3]))))
	# p6 = plt.bar(ind, tuples[5], width, color='#c6dbef',label='1280x533',edgecolor='black',hatch="/",
	#              bottom=tuple(map(sum,zip(tuples[0],tuples[1],tuples[2],tuples[3],tuples[4]))))

	plt.ylabel('Percentage of Time')
	plt.axvline(x=3.5,color='black',linestyle='--')
	plt.axvline(x=7.5, color='black',linestyle='--')
	plt.axvline(x=11.5, color='black',linestyle='--')
	plt.axvline(x=15.5, color='black',linestyle='--')
	plt.xticks(ind, ('ATT','Sprint','TMobile','Verizon','ATT','Sprint','TMobile','Verizon','ATT','Sprint','TMobile','Verizon', 'ATT', 'Sprint','TMobile','Verizon','WiFi','WiFi VPN'))
	plt.yticks(np.arange(0, 110, 20))
	


	# plt.legend(bbox_to_anchor=(0,1.12,1,0.2),mode="expand" , ncol=3, loc="lower left")
	plt.xticks(rotation=45,horizontalalignment="right")
	fig.tight_layout()
	plt.annotate('Exposed',
            xy=(120, 280), xycoords='figure pixels')

	plt.annotate('Max Data',
            xy=(250, 280), xycoords='figure pixels')

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





