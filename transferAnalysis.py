import sys, subprocess
import matplotlib.pyplot as plt

def xputCDF(pcap, xputInterval=0.25, outfile='kir_transfer'):
    command = ['tshark', '-r', pcap, '-T', 'fields', 
               '-e', 'frame.number', 
               '-e', 'frame.protocols', 
               '-e', 'frame.time_relative', 
               '-e', 'frame.len', 
               '-e', 'tcp.analysis.retransmission',
               ]
     
    p              = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err    = p.communicate()

    xput = []
    
    total = 0.0
    all   = 0
    i     = 1
    
    for l in output.splitlines():
        l = l.split()
        
        #Skip retransmissions
        try:
            l[4]
            continue
        except:
            pass
        
        ts = float(l[2])
        b  = float(l[3])
        
        if ts <= i*xputInterval:
            total += b
            all   += b
        else:
            xput.append(total/xputInterval)
            total = b
            i += 1
            
        
    xput.append(total/(ts-(i-1)*xputInterval))
    
    #Make it Mbits/sec
    xput = map(lambda x: x*8/1000000.0, xput)
    
    x, y = list2CDF(xput)
    
    plt.plot(x, y, linewidth=2)

    plt.legend(loc='best')
    plt.grid()
    plt.xlabel('Xput (Mbps)')
    plt.ylabel('CDF')
    plt.savefig(outfile + '_cdf.png')
        
def parseTsharkTransferOutput(output):
    '''
    ************ WORKS WITH tshark 1.12.1 ONLY ************
    '''
    x = []
    y = []
    lines       = output.splitlines()
    
    total = 0
    
    for l in lines:
        if '<>' not in l:
            continue
        
        l      = l.replace('|', '')
        l      = l.replace('<>', '')
        parsed = map(float, l.split())
        end    = parsed[1]
        bytes  = parsed[-1]
        
        total += bytes 
        
        x.append(end)
        y.append(total)
        
    #converting to Mbits/sec
    y = map(lambda z: z/1000000.0, y)
    
    return x, y 

def doTransfers(pcap, xputInterval=0.25, outfile='kir_transfer'):
    p           = subprocess.Popen(['tshark', '-r', pcap, '-qz', 'io,stat,'+str(xputInterval)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    x, y        = parseTsharkTransferOutput(output)
    plt.plot(x, y, linewidth=2)

    plt.legend(loc='best')
    plt.grid()
    plt.xlabel('Time (second)')
    plt.ylabel('Cumulative transfer (Mbits)')
    plt.savefig(outfile+'_transfer.png')
    
def list2CDF(xput):
    xput = sorted(xput)
    
    x   = [0]
    y   = [0]
    
    for i in range(len(xput)):
        x.append(xput[i])
        y.append(float(i+1)/len(xput))
    
    return x, y

pcap    = sys.argv[1]
outfile = sys.argv[2]

print pcap, outfile

doTransfers(pcap, outfile=outfile)
plt.clf()
xputCDF(pcap, outfile=outfile)
