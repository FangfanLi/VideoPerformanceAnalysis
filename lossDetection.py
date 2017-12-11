import sys
import subprocess
import matplotlib.pyplot as plt
import doTcpTrace

def getRetransmissionTimes(pcapFile):
    command     = ['tshark', '-r', pcapFile, '-T', 'fields', '-e', 'frame.time_relative', '-e', 'tcp.analysis.retransmission']
    p           = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    
    times = []
    lines = output.split('\n')
    
    for l in lines:
        try:
            if l.split()[1] == '1':
                times.append(l.split()[0])
        except:
            continue
    
    return times

pcapFile = sys.argv[1]

ts, xputs = doTcpTrace.doXputs(pcapFile, xputInterval=0.1)
times     = getRetransmissionTimes(pcapFile)

for t in times:
    plt.axvline(t, ymax=1, color='r', alpha=0.5)

plt.plot(ts, xputs, color='b', alpha=0.7, linewidth=5)
plt.show()