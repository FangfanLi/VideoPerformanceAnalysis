import subprocess
import sys
import ipaddress
import numpy
import copy

def isPrivate(ip):
    ip = unicode(ip)
    return ipaddress.ip_address(ip).is_private

def doXputs(pcapFile, xputInterval=0.25):
    #Run tshark
    cmd         = ['tshark', '-r', pcapFile, '-qz', 'io,stat,'+str(xputInterval)]
    p           = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    
    #Parse tshark output
    lines       = output.splitlines()
    end         = lines[4].partition('Duration:')[2].partition('secs')[0].replace(' ', '')
    lines[-2]   = lines[-2].replace('Dur', end)

    ts   = []
    xput = []

    for l in lines:
        if '<>' not in l:
            continue

        l      = l.replace('|', '')
        l      = l.replace('<>', '')
        parsed = map(float, l.split())
        
        start  = float(parsed[0])
        end    = float(parsed[1])
        dur    = end - start

        if dur == 0:
            continue
        
        ts.append(end)
        xput.append( float(parsed[-1])/dur )

    xput = map(lambda x: x*8/1000000.0, xput)

    return ts, xput

def getNumberOfTcpResets(pcapFile):
    cmd         = ['tshark', '-r', pcapFile, '-Y', 'tcp.flags.reset==1']
    p           = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    
    return len(output.split('n'))

class Connection(object):
    '''
    TCPTRACE gives separate stats for each connection (a.k.a stream) in the trace. 
    
    This class stores tcptrace stats for a single stream
    '''
    def __init__(self, statsText=None):
        self.connNum     = None
        self.connStats   = {}
        self.detailStats = {'client2server' : {},
                            'server2client' : {}}
        if statsText:
            self.parseTcptraceOutput(statsText)
    
    def parseTcptraceOutput(self, statsText):
        self.connNum = int(statsText[0].rpartition(':')[0].split(' ')[2])
        
        [aIP, aPort] = statsText[1].partition(':')[2].strip().split(':')
        [bIP, bPort] = statsText[2].partition(':')[2].strip().split(':')
        
        host1 = statsText[1].partition(':')[0].split(' ')[1]
        host2 = statsText[2].partition(':')[0].split(' ')[1]
        
        if isPrivate(aIP):
            self.serverName, self.serverIP, self.serverPort = host1, aIP, aPort
            self.clientName, self.clientIP, self.clientPort = host2, bIP, bPort
        else:
            self.clientName, self.serverIP, self.serverPort = host1, aIP, aPort
            self.serverName, self.serverIP, self.serverPort = host2, bIP, bPort
        
        columns = map(lambda x: x.strip(), statsText[9][:-1].split(':'))

        if columns[0] == '{}->{}'.format(self.clientName, self.serverName):
            self.client2serverColumn = 0
            self.server2clientColumn = 1
        else:
            self.client2serverColumn = 1
            self.server2clientColumn = 0
        
        for l in statsText[3:10]:
            self.connStats[l.split(':')[0].strip()] = l.split(':')[1].strip()
            
        for l in statsText[10:]:
            key    = l.partition(':')[0]
            values = [l.partition(':')[2].partition(key+':')[0].strip(), l.partition(':')[2].partition(key+':')[2].strip()]
            
            self.detailStats['client2server'][key] = values[self.client2serverColumn]
            self.detailStats['server2client'][key] = values[self.server2clientColumn]
            
class TcptraceResult(object):
    '''
    A class which stores "tcptrace" stats for a whole pcap file
    '''
    def __init__(self, pcapPath):
        self.pcapPath            = pcapPath
        self.connections         = []
        self.connectionsFiltered = []
        self.includedInFiltered  = []
        self.totalXputMin_tshark = None
        self.totalXputMax_tshark = None
        self.totalXputAvg_tshark = None
        self.totalRetransmits    = None
        self.totalOutOfOrder     = None
        self.clientMinWinAdv     = None
        self.clientMaxWinAdv     = None
        self.serverMinWinAdv     = None
        self.serverMaxWinAdv     = None
        self.numberOfTcpResets   = None

    def doTotals(self):
        '''
        Produce some stats for the whole pcap file considering all the connections
        '''
        self.totalDataPackets       = sum([int(x.detailStats['server2client']['actual data pkts']) for x in self.connections]
                                          +
                                          [int(x.detailStats['client2server']['actual data pkts']) for x in self.connections])
        
        self.totalRetransmits       = sum([int(x.detailStats['server2client']['rexmt data pkts']) for x in self.connections]
                                          +
                                          [int(x.detailStats['client2server']['rexmt data pkts']) for x in self.connections])
    
        self.totalOutOfOrder        = sum([int(x.detailStats['server2client']['outoforder pkts']) for x in self.connections]
                                          +
                                          [int(x.detailStats['client2server']['outoforder pkts']) for x in self.connections])
        
        self.clientMinWinAdv        = min([int(x.detailStats['client2server']['min win adv'].split()[0]) for x in self.connections])
        self.clientMaxWinAdv        = max([int(x.detailStats['client2server']['max win adv'].split()[0]) for x in self.connections])
        self.serverMinWinAdv        = min([int(x.detailStats['server2client']['min win adv'].split()[0]) for x in self.connections])
        self.serverMaxWinAdv        = max([int(x.detailStats['server2client']['max win adv'].split()[0]) for x in self.connections])
        
        self.server2clientMinRTT    = min([float(x.detailStats['server2client']['RTT min'].split()[0]) for x in self.connections])
        self.server2clientMaxRTT    = max([float(x.detailStats['server2client']['RTT max'].split()[0]) for x in self.connections])
        
        self.server2clientAvgRTTavg = round(numpy.average([float(x.detailStats['server2client']['RTT avg'].split()[0]) for x in self.connections]), 2)
        self.server2clientAvgRTTstd = round(numpy.average([float(x.detailStats['server2client']['RTT stdev'].split()[0]) for x in self.connections]), 2)
        
    def doTotalsFiltered(self, factor=0.5):
        '''
        Basically does the same as doTotals(), but only for major streams, i.e. streams that carry the main data
        
        Major streams: 1) calculate packetCountThreshold which is the number of packets in the largest stream
                       2) any stream with more than factor*packetCountThreshold is considered major
        '''
        packetCountThreshold = max([int(x.connStats['total packets']) for x in self.connections])
        
        for conn in self.connections:
            if int(conn.connStats['total packets']) > factor*packetCountThreshold:
                self.connectionsFiltered.append(conn)
                self.includedInFiltered.append(conn.connNum)
        
          
        self.totalDataPacketsFiltered       = sum([int(x.detailStats['server2client']['actual data pkts']) for x in self.connectionsFiltered]
                                                  +
                                                  [int(x.detailStats['client2server']['actual data pkts']) for x in self.connectionsFiltered])
        
        self.totalServerDataPacketsFiltered = sum([int(x.detailStats['server2client']['actual data pkts']) for x in self.connectionsFiltered])
        
        self.totalClientDataPacketsFiltered = sum([int(x.detailStats['client2server']['actual data pkts']) for x in self.connectionsFiltered])
        
        self.totalRetransmitsFiltered       = sum([int(x.detailStats['server2client']['rexmt data pkts']) for x in self.connectionsFiltered]
                                                  +
                                                  [int(x.detailStats['client2server']['rexmt data pkts']) for x in self.connectionsFiltered])
    
        self.totalOutOfOrderFiltered        = sum([int(x.detailStats['server2client']['outoforder pkts']) for x in self.connectionsFiltered]
                                                  +
                                                  [int(x.detailStats['client2server']['outoforder pkts']) for x in self.connectionsFiltered])
        
        self.clientMinWinAdvFiltered        = min([int(x.detailStats['client2server']['min win adv'].split()[0]) for x in self.connectionsFiltered])
        self.clientMaxWinAdvFiltered        = max([int(x.detailStats['client2server']['max win adv'].split()[0]) for x in self.connectionsFiltered])
        self.serverMinWinAdvFiltered        = min([int(x.detailStats['server2client']['min win adv'].split()[0]) for x in self.connectionsFiltered])
        self.serverMaxWinAdvFiltered        = max([int(x.detailStats['server2client']['max win adv'].split()[0]) for x in self.connectionsFiltered])
        
        self.server2clientMinRTTFiltered    = min([float(x.detailStats['server2client']['RTT min'].split()[0]) for x in self.connectionsFiltered])
        self.server2clientMaxRTTFiltered    = max([float(x.detailStats['server2client']['RTT max'].split()[0]) for x in self.connectionsFiltered])
        
        self.server2clientAvgRTTavgFiltered = round(numpy.average([float(x.detailStats['server2client']['RTT avg'].split()[0]) for x in self.connectionsFiltered]), 2)
        self.server2clientAvgRTTstdFiltered = round(numpy.average([float(x.detailStats['server2client']['RTT stdev'].split()[0]) for x in self.connectionsFiltered]), 2)
    
    def doXputStats(self):
        ts, xput  = doXputs(self.pcapPath)
   
        self.totalXputMin_tshark = round(min(xput), 2)
        self.totalXputMax_tshark = round(max(xput), 2)
        self.totalXputAvg_tshark = round(numpy.average(xput), 2)
    
    def getNumberOfTcpResets(self):
        self.numberOfTcpResets = getNumberOfTcpResets(self.pcapPath)
        
def doOne(pcapFile):
    #1-Create tcptrace result object
    tcptraceRes = TcptraceResult(pcapFile)
    
    #2-Get xput and reset packet info using tshark
#     tcptraceRes.doXputStats()
#     tcptraceRes.getNumberOfTcpResets()
    
    #3-Run tcptrace and get the output
    cmd         = ['tcptrace', '-l', '-n', '-r', '-W', pcapFile]
    p           = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()
    output      = output.split('\n')
    
    #4-Find the begining of stats
    for i in range(len(output)):
        l = output[i].strip()
        
        if l.endswith('TCP connections traced:'):
            index = i
            break
    
    #5-Parse results one connection at a time and add to the result object
    statsText = []
    for i in range(index+1, len(output)):
        l = output[i].strip()
        
        if not l.startswith('====='):
            statsText.append(l)
        else:
            conn = Connection(statsText)
            tcptraceRes.connections.append(conn)
            statsText = []
    
    tcptraceRes.doTotals()
    tcptraceRes.doTotalsFiltered()
    
    return tcptraceRes

def doBatch(pcapFiles):
    all = {}
    for pcapFile in pcapFiles:
        print 'Doing:', pcapFile
        tcptraceRes = doOne(pcapFile)
        all[ pcapFile.rpartition('/')[2] ] = tcptraceRes
        
#         for conn in sorted(tcptraceRes.connections, key=lambda x: x.connNum):
#             print ',\t'.join(map(str, [conn.connNum, conn.detailStats['server2client']['throughput']])) 
        print '\tincludedInFiltered:', tcptraceRes.includedInFiltered
        print '\ttotalDataPacketsFiltered:', tcptraceRes.totalDataPacketsFiltered
        print '\ttotalServerDataPacketsFiltered:', tcptraceRes.totalServerDataPacketsFiltered
        print '\ttotalClientDataPacketsFiltered:', tcptraceRes.totalClientDataPacketsFiltered
#         print '\t', tcptraceRes.totalXputMin_tshark, tcptraceRes.totalXputMax_tshark, tcptraceRes.totalXputAvg_tshark
#         print '\t', tcptraceRes.numberOfTcpResets
        print '\ttotalRetransmits:', tcptraceRes.totalRetransmits
        print '\ttotalOutOfOrder:', tcptraceRes.totalOutOfOrder
        print '\t', tcptraceRes.server2clientMinRTT, tcptraceRes.server2clientMaxRTT, tcptraceRes.server2clientAvgRTTavg, tcptraceRes.server2clientAvgRTTstd
        print '\t', tcptraceRes.server2clientMinRTTFiltered, tcptraceRes.server2clientMaxRTTFiltered, tcptraceRes.server2clientAvgRTTavgFiltered, tcptraceRes.server2clientAvgRTTstdFiltered
#         print '\t', tcptraceRes.clientMinWinAdv, tcptraceRes.clientMaxWinAdv, tcptraceRes.serverMinWinAdv, tcptraceRes.serverMaxWinAdv
#         print '\t', tcptraceRes.clientMinWinAdvFiltered, tcptraceRes.clientMaxWinAdvFiltered, tcptraceRes.serverMinWinAdvFiltered, tcptraceRes.serverMaxWinAdvFiltered
        print '\n'

def main():
    doBatch(sys.argv[1:])
    
if __name__ == '__main__':
    main()    