'''
jsonFile      : is JSON extracted from DB by the following query:
                SELECT incomingTime, userID, testID, historyCount, extraString, replayName, xput_min, xput_max, xput_avg, rtt_min, rtt_max, rtt_avg FROM ResultsDB.replays WHERE incomingTime > "2015-12-01" ORDER BY p_id DESC;

toConsiderFile: tab separated which is copy paste from sheet like this: https://docs.google.com/spreadsheets/d/1oPEPL5hbLkGJVlG1RcZwa3tr6KTZi8pRQirqIuWyy_k/edit?usp=sharing
                Only the first 4 columns:
                [userID] [historyCount] [BingeOn] [tether]
                
Basically for BingeOn experiments we need ALL replay after Dec-01-2015 and the tests we want to consider (Me + Christo + Ethan + Luis)

So for jsonFile, run this:

    SELECT incomingTime, userID, replayName, testID, historyCount, extraString, xput_min, xput_max, xput_avg, rtt_min, rtt_max, rtt_avg FROM ResultsDB.replays 
    WHERE incomingTime > "2015-12-01" 
    ORDER BY p_id DESC;

And for toConsider, use all you have! So run:

    python plotXputScatter.py ../data/replays_after_Dec_01_2015.json ../data/replays_*_toConsider.txt
'''
import matplotlib.pyplot as plt
try:
    import seaborn as sns; sns.set()
except:
    pass
import sys
import json
import glob
import doTcpTrace

def loadDBjson(jsonFile):

    with open(jsonFile, 'r') as f:
        string = f.read()
    
    string  = string.strip().replace("'", "\"")
    string  = string.strip().replace("NULL", "\"NULL\"")
    
    return json.loads(string)

def readToConsiderFile(toConsiderFile, toCondider):
    with open(toConsiderFile, 'r') as f:
        lines = f.readlines()

    for l in lines:
        userID        = l.strip().split('\t')[0]
        historyCounts = l.strip().split('\t')[1].split(',')
        bingeon       = l.strip().split('\t')[2]
        tether        = l.strip().split('\t')[3]

        try:
            toCondider[userID]
        
        except:
            toCondider[userID] = {}
        
        finally:
            for hc in historyCounts:
                hc = hc.split('-')

                if len(hc) == 2:
                    for i in range( int(hc[0]), int(hc[1])+1 ):
                        toCondider[userID][i] = (bingeon, tether)
                
                elif not hc[0]:
                    continue
                
                else:
                    toCondider[userID][int(hc[0])] = (bingeon, tether)
    
    return toCondider

def plot_xput_vs_rtt(jsonFiles, toConsiderFiles, app=None, title=None):
    
    inJson     = []
    toCondider = {}
    
    for file in jsonFiles:
        inJson += loadDBjson(file)
    
    for file in toConsiderFiles:
        toCondider = readToConsiderFile(file, toCondider)
    
    bingeon_ON_tether_YES_xput  = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_ON_tether_YES_rtt   = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_ON_tether_NO_xput   = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_ON_tether_NO_rtt    = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_YES_xput = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_YES_rtt  = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_NO_xput  = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_NO_rtt   = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    
    for r in inJson:
        try:
            (bingeon, tether) = toCondider[r['userID']][r['historyCount']]
        except KeyError:
            continue
        
        if app and (not r['replayName'].startswith(app)):
            continue
        
        if r['xput_avg'] == -1:
            continue
        
        if bingeon.lower() == 'on' and tether.lower() == 'yes':
            if r['testID'].startswith('NOVPN'):
                bingeon_ON_tether_YES_xput['NOVPN'].append( r['xput_avg'])
                bingeon_ON_tether_YES_rtt['NOVPN'].append( r['rtt_avg']) 
            
            if r['testID'].startswith('VPN'):
                bingeon_ON_tether_YES_xput['VPN'].append(r['xput_avg'])
                bingeon_ON_tether_YES_rtt['VPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('RANDOM'):
                bingeon_ON_tether_YES_xput['RANDOM'].append(r['xput_avg'])
                bingeon_ON_tether_YES_rtt['RANDOM'].append(r['rtt_avg'])
                
        elif bingeon.lower() == 'on' and tether.lower() == 'no':
            if r['testID'].startswith('NOVPN'):
                bingeon_ON_tether_NO_xput['NOVPN'].append(r['xput_avg'])
                bingeon_ON_tether_NO_rtt['NOVPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('VPN'):
                bingeon_ON_tether_NO_xput['VPN'].append(r['xput_avg'])
                bingeon_ON_tether_NO_rtt['VPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('RANDOM'):
                bingeon_ON_tether_NO_xput['RANDOM'].append(r['xput_avg'])
                bingeon_ON_tether_NO_rtt['RANDOM'].append(r['rtt_avg'])
        
        elif bingeon.lower() == 'off' and tether.lower() == 'yes':
            if r['testID'].startswith('NOVPN'):
                bingeon_OFF_tether_YES_xput['NOVPN'].append(r['xput_avg'])
                bingeon_OFF_tether_YES_rtt['NOVPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('VPN'):
                bingeon_OFF_tether_YES_xput['VPN'].append(r['xput_avg'])
                bingeon_OFF_tether_YES_rtt['VPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('RANDOM'):
                bingeon_OFF_tether_YES_xput['RANDOM'].append(r['xput_avg'])
                bingeon_OFF_tether_YES_rtt['RANDOM'].append(r['rtt_avg'])
                
        elif bingeon.lower() == 'off' and tether.lower() == 'no':
            if r['testID'].startswith('NOVPN'):
                bingeon_OFF_tether_NO_xput['NOVPN'].append(r['xput_avg'])
                bingeon_OFF_tether_NO_rtt['NOVPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('VPN'):
                bingeon_OFF_tether_NO_xput['VPN'].append(r['xput_avg'])
                bingeon_OFF_tether_NO_rtt['VPN'].append(r['rtt_avg'])
            
            if r['testID'].startswith('RANDOM'):
                bingeon_OFF_tether_NO_xput['RANDOM'].append(r['xput_avg'])
                bingeon_OFF_tether_NO_rtt['RANDOM'].append(r['rtt_avg'])
        
        else:
            print 'WHAT?', (bingeon, tether)
            sys.exit()
    
    fig, ax = plt.subplots(2, 1, sharex=True, sharey=True, figsize=plt.figaspect(0.3))

    ax[0].plot(bingeon_ON_tether_YES_xput['NOVPN'], bingeon_ON_tether_YES_rtt['NOVPN']    , linestyle='None', alpha=0.5, color='r', marker='o', markersize=10, label='NOVPN_BO-ON')
    ax[0].plot(bingeon_ON_tether_YES_xput['VPN'], bingeon_ON_tether_YES_rtt['VPN']        , linestyle='None', alpha=0.5, color='r', marker='^', markersize=10, label='VPN_BO-ON')
    ax[0].plot(bingeon_ON_tether_YES_xput['RANDOM'], bingeon_ON_tether_YES_rtt['RANDOM']  , linestyle='None', alpha=0.5, color='r', marker='*', markersize=15, label='RANDOM_BO-ON')
      
    ax[0].plot(bingeon_OFF_tether_YES_xput['NOVPN'], bingeon_OFF_tether_YES_rtt['NOVPN']  , linestyle='None', alpha=0.5, color='g', marker='o', markersize=10, label='NOVPN_BO-OFF')
    ax[0].plot(bingeon_OFF_tether_YES_xput['VPN'], bingeon_OFF_tether_YES_rtt['VPN']      , linestyle='None', alpha=0.5, color='g', marker='^', markersize=10, label='VPN_BO-OFF')
    ax[0].plot(bingeon_OFF_tether_YES_xput['RANDOM'], bingeon_OFF_tether_YES_rtt['RANDOM'], linestyle='None', alpha=0.5, color='g', marker='*', markersize=15, label='RANDOM_BO-OFF')
    
    ax[1].plot(bingeon_ON_tether_NO_xput['NOVPN'], bingeon_ON_tether_NO_rtt['NOVPN']      , linestyle='None', alpha=0.5, color='r', marker='o', markersize=10, label='NOVPN_BO-ON')
    ax[1].plot(bingeon_ON_tether_NO_xput['VPN'], bingeon_ON_tether_NO_rtt['VPN']          , linestyle='None', alpha=0.5, color='r', marker='^', markersize=10, label='VPN_BO-ON')
    ax[1].plot(bingeon_ON_tether_NO_xput['RANDOM'], bingeon_ON_tether_NO_rtt['RANDOM']    , linestyle='None', alpha=0.5, color='r', marker='*', markersize=15, label='RANDOM_BO-ON')
      
    ax[1].plot(bingeon_OFF_tether_NO_xput['NOVPN'], bingeon_OFF_tether_NO_rtt['NOVPN']    , linestyle='None', alpha=0.5, color='g', marker='o', markersize=10, label='NOVPN_BO-OFF')
    ax[1].plot(bingeon_OFF_tether_NO_xput['VPN'], bingeon_OFF_tether_NO_rtt['VPN']        , linestyle='None', alpha=0.5, color='g', marker='^', markersize=10, label='VPN_BO-OFF')
    ax[1].plot(bingeon_OFF_tether_NO_xput['RANDOM'], bingeon_OFF_tether_NO_rtt['RANDOM']  , linestyle='None', alpha=0.5, color='g', marker='*', markersize=15, label='RANDOM_BO-OFF')

    ax[0].axvline([1.6], linewidth=5, alpha=0.3)
    ax[1].axvline([1.6], linewidth=5, alpha=0.3)
    
    ax[0].set_title('{}--Tether'.format(app))
    ax[1].set_title('{}--Direct'.format(app))
     
    ax[0].set_ylabel('Average RTT (s)', fontsize=12)
    ax[1].set_ylabel('Average RTT (s)', fontsize=12)
    ax[1].set_xlabel('Average Xput (Mbps)', fontsize=12)

    ax[0].legend(fontsize=8)
    ax[1].legend(fontsize=8)
    
    ax[0].grid(True)
    ax[1].grid(True)
    
    if not title:
        title = 'scatter_xput_rtt_{}.png'.format(app)
        
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(title)
    
    json.dump(bingeon_ON_tether_YES_xput    , open('{}_bingeon_ON_tether_YES_xput.json'.format(app) , 'w'))
    json.dump(bingeon_ON_tether_YES_rtt     , open('{}_bingeon_ON_tether_YES_rtt.json'.format(app)  , 'w'))
    json.dump(bingeon_ON_tether_NO_xput     , open('{}_bingeon_ON_tether_NO_xput.json'.format(app)  , 'w'))
    json.dump(bingeon_ON_tether_NO_rtt      , open('{}_bingeon_ON_tether_NO_rtt.json'.format(app)   , 'w'))
    json.dump(bingeon_OFF_tether_YES_xput   , open('{}_bingeon_OFF_tether_YES_xput.json'.format(app), 'w'))
    json.dump(bingeon_OFF_tether_YES_rtt    , open('{}_bingeon_OFF_tether_YES_rtt.json'.format(app) , 'w'))
    json.dump(bingeon_OFF_tether_NO_xput    , open('{}_bingeon_OFF_tether_NO_xput.json'.format(app) , 'w'))
    json.dump(bingeon_OFF_tether_NO_rtt     , open('{}_bingeon_OFF_tether_NO_rtt.json'.format(app)  , 'w'))

def plot_xput_vs_retransmit(jsonFiles, toConsiderFiles, app=None, title=None):
    
    inJson     = []
    toCondider = {}
    
    for file in jsonFiles:
        inJson += loadDBjson(file)
    
    for file in toConsiderFiles:
        toCondider = readToConsiderFile(file, toCondider)
    
    bingeon_ON_tether_YES_xput  = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_ON_tether_YES_reT   = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_ON_tether_NO_xput   = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_ON_tether_NO_reT    = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_YES_xput = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_YES_reT  = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_NO_xput  = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    bingeon_OFF_tether_NO_reT   = {'NOVPN':[], 'VPN':[], 'RANDOM':[]}
    
    for r in inJson:
        try:
            (bingeon, tether) = toCondider[r['userID']][r['historyCount']]
        except KeyError:
            continue
        
        if app and (not r['replayName'].startswith(app)):
            continue
        
        if r['xput_avg'] == -1:
            continue
        
        x = '/net/data/record-replay/ServersBU/*/RecordReplay/ReplayDumps/{}/tcpdumpsResults/dump_server_{}_*_{}_*_{}_out.pcap'.format(r['userID'], r['userID'], r['testID'], r['historyCount'])
        pcapPath = glob.glob(x)
        assert(len(pcapPath) == 1)
        tcptraceRes = doTcpTrace.doOne(pcapPath[0])
        print 'Did:', r['userID'], r['testID'], r['historyCount'], '\t', tcptraceRes.totalRetransmits, '\t', tcptraceRes.totalDataPackets
        
        if bingeon.lower() == 'on' and tether.lower() == 'yes':
            if r['testID'].startswith('NOVPN'):
                bingeon_ON_tether_YES_xput['NOVPN'].append(r['xput_avg'])
                bingeon_ON_tether_YES_reT['NOVPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets) 
            
            if r['testID'].startswith('VPN'):
                bingeon_ON_tether_YES_xput['VPN'].append(r['xput_avg'])
                bingeon_ON_tether_YES_reT['VPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('RANDOM'):
                bingeon_ON_tether_YES_xput['RANDOM'].append(r['xput_avg'])
                bingeon_ON_tether_YES_reT['RANDOM'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
                
        elif bingeon.lower() == 'on' and tether.lower() == 'no':
            if r['testID'].startswith('NOVPN'):
                bingeon_ON_tether_NO_xput['NOVPN'].append(r['xput_avg'])
                bingeon_ON_tether_NO_reT['NOVPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('VPN'):
                bingeon_ON_tether_NO_xput['VPN'].append(r['xput_avg'])
                bingeon_ON_tether_NO_reT['VPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('RANDOM'):
                bingeon_ON_tether_NO_xput['RANDOM'].append(r['xput_avg'])
                bingeon_ON_tether_NO_reT['RANDOM'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
        
        elif bingeon.lower() == 'off' and tether.lower() == 'yes':
            if r['testID'].startswith('NOVPN'):
                bingeon_OFF_tether_YES_xput['NOVPN'].append(r['xput_avg'])
                bingeon_OFF_tether_YES_reT['NOVPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('VPN'):
                bingeon_OFF_tether_YES_xput['VPN'].append(r['xput_avg'])
                bingeon_OFF_tether_YES_reT['VPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('RANDOM'):
                bingeon_OFF_tether_YES_xput['RANDOM'].append(r['xput_avg'])
                bingeon_OFF_tether_YES_reT['RANDOM'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
                
        elif bingeon.lower() == 'off' and tether.lower() == 'no':
            if r['testID'].startswith('NOVPN'):
                bingeon_OFF_tether_NO_xput['NOVPN'].append(r['xput_avg'])
                bingeon_OFF_tether_NO_reT['NOVPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('VPN'):
                bingeon_OFF_tether_NO_xput['VPN'].append(r['xput_avg'])
                bingeon_OFF_tether_NO_reT['VPN'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
            
            if r['testID'].startswith('RANDOM'):
                bingeon_OFF_tether_NO_xput['RANDOM'].append(r['xput_avg'])
                bingeon_OFF_tether_NO_reT['RANDOM'].append(float(tcptraceRes.totalRetransmits)/tcptraceRes.totalDataPackets)
        
        else:
            print 'WHAT?', (bingeon, tether)
            sys.exit()
    
    fig, ax = plt.subplots(2, 1, sharex=True, sharey=True, figsize=plt.figaspect(0.3))
    
    ax[0].plot(bingeon_ON_tether_YES_xput['NOVPN'], bingeon_ON_tether_YES_reT['NOVPN']    , linestyle='None', alpha=0.5, color='r', marker='o', markersize=10, label='NOVPN_BO-ON')
    ax[0].plot(bingeon_ON_tether_YES_xput['VPN'], bingeon_ON_tether_YES_reT['VPN']        , linestyle='None', alpha=0.5, color='r', marker='^', markersize=10, label='VPN_BO-ON')
    ax[0].plot(bingeon_ON_tether_YES_xput['RANDOM'], bingeon_ON_tether_YES_reT['RANDOM']  , linestyle='None', alpha=0.5, color='r', marker='*', markersize=15, label='RANDOM_BO-ON')
      
    ax[0].plot(bingeon_OFF_tether_YES_xput['NOVPN'], bingeon_OFF_tether_YES_reT['NOVPN']  , linestyle='None', alpha=0.5, color='g', marker='o', markersize=10, label='NOVPN_BO-OFF')
    ax[0].plot(bingeon_OFF_tether_YES_xput['VPN'], bingeon_OFF_tether_YES_reT['VPN']      , linestyle='None', alpha=0.5, color='g', marker='^', markersize=10, label='VPN_BO-OFF')
    ax[0].plot(bingeon_OFF_tether_YES_xput['RANDOM'], bingeon_OFF_tether_YES_reT['RANDOM'], linestyle='None', alpha=0.5, color='g', marker='*', markersize=15, label='RANDOM_BO-OFF')

    ax[1].plot(bingeon_ON_tether_NO_xput['NOVPN'], bingeon_ON_tether_NO_reT['NOVPN']      , linestyle='None', alpha=0.5, color='r', marker='o', markersize=10, label='NOVPN_BO-ON')
    ax[1].plot(bingeon_ON_tether_NO_xput['VPN'], bingeon_ON_tether_NO_reT['VPN']          , linestyle='None', alpha=0.5, color='r', marker='^', markersize=10, label='VPN_BO-ON')
    ax[1].plot(bingeon_ON_tether_NO_xput['RANDOM'], bingeon_ON_tether_NO_reT['RANDOM']    , linestyle='None', alpha=0.5, color='r', marker='*', markersize=15, label='RANDOM_BO-ON')
      
    ax[1].plot(bingeon_OFF_tether_NO_xput['NOVPN'], bingeon_OFF_tether_NO_reT['NOVPN']    , linestyle='None', alpha=0.5, color='g', marker='o', markersize=10, label='NOVPN_BO-OFF')
    ax[1].plot(bingeon_OFF_tether_NO_xput['VPN'], bingeon_OFF_tether_NO_reT['VPN']        , linestyle='None', alpha=0.5, color='g', marker='^', markersize=10, label='VPN_BO-OFF')
    ax[1].plot(bingeon_OFF_tether_NO_xput['RANDOM'], bingeon_OFF_tether_NO_reT['RANDOM']  , linestyle='None', alpha=0.5, color='g', marker='*', markersize=15, label='RANDOM_BO-OFF')

    ax[0].axvline([1.6], linewidth=5, alpha=0.3)
    ax[1].axvline([1.6], linewidth=5, alpha=0.3)
    
    ax[0].set_title('{}--Tether'.format(app))
    ax[1].set_title('{}--Direct'.format(app))
     
    ax[0].set_ylabel('#Retransmits', fontsize=12)
    ax[1].set_ylabel('#Retransmits', fontsize=12)
    ax[1].set_xlabel('Average Xput (Mbps)', fontsize=12)
    
    ax[1].legend(fontsize=8)
    ax[0].legend(fontsize=8)
    
    ax[1].grid(True)
    ax[0].grid(True)
    
    if not title:
        title = 'scatter_xput_reT_{}.png'.format(app)
    
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(title)
    
    json.dump(bingeon_ON_tether_YES_xput    , open('{}_bingeon_ON_tether_YES_xput.json'.format(app) , 'w'))
    json.dump(bingeon_ON_tether_YES_reT     , open('{}_bingeon_ON_tether_YES_reT.json'.format(app)  , 'w'))
    json.dump(bingeon_ON_tether_NO_xput     , open('{}_bingeon_ON_tether_NO_xput.json'.format(app)  , 'w'))
    json.dump(bingeon_ON_tether_NO_reT      , open('{}_bingeon_ON_tether_NO_reT.json'.format(app)   , 'w'))
    json.dump(bingeon_OFF_tether_YES_xput   , open('{}_bingeon_OFF_tether_YES_xput.json'.format(app), 'w'))
    json.dump(bingeon_OFF_tether_YES_reT    , open('{}_bingeon_OFF_tether_YES_reT.json'.format(app) , 'w'))
    json.dump(bingeon_OFF_tether_NO_xput    , open('{}_bingeon_OFF_tether_NO_xput.json'.format(app) , 'w'))
    json.dump(bingeon_OFF_tether_NO_reT     , open('{}_bingeon_OFF_tether_NO_reT.json'.format(app)  , 'w'))

jsonFiles       = []
toConsiderFiles = []

app = 'netflix'
# app = 'youtube'

for file in sys.argv[1:]:
    if file.endswith('.json'):
        jsonFiles.append(file)
    elif file.endswith('.txt'):
        toConsiderFiles.append(file)


plot_xput_vs_rtt(jsonFiles, toConsiderFiles, app=app)
plot_xput_vs_retransmit(jsonFiles, toConsiderFiles, app=app)
