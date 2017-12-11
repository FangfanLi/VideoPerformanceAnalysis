'''
by: Arash Molavi Kakhki (arash@ccs.neu.edu)

The first four events of the events list are always the following (in order):
    event[0] = UNSTARTED
    event[1] = BUFFERING
    event[2] = QualityChange
    event[3] = PLAYING
'''

import sys, json, numpy

errors  = []
results = {'On':{}, 'Off':{}}

for file in sys.argv[1:]:

    res = json.load(open(file, 'r'))
    try:
        assert(res['events'][0]['event'] == 'UNSTARTED')
        assert(res['events'][1]['event'] == 'BUFFERING')
        assert(res['events'][2]['event'] == 'QualityChange')
        assert(res['events'][3]['event'] == 'PLAYING')
    except:
        errors.append(file)
        continue
        
    network             = res['network']
    bingeon             = res['bingeon']
    tether              = res['tether']
    desiredQuality      = res['desiredQuality']
    initialQuality      = res['events'][2]['event.data']   
    finalFractionLoaded = res['events'][-1]['VideoLoadedFraction']   
    timeToStartPlaying  = res['events'][3]['time'] - res['events'][0]['time']
    
    endQuality          = initialQuality

    rebufferCount       = 0
    qualityChangeCount  = 0

    bufferingTime       = 0
    playingTime         = 0
    lastTime            = res['events'][1]['time']
    mode                = 'playing'
    
    for e in res['events']:
        if e['event'] == 'QualityChange':
            endQuality          = e['event.data']
            qualityChangeCount += 1
        elif e['event'] == 'BUFFERING':
            rebufferCount += 1
            playingTime   += (e['time'] - lastTime)
            lastTime       = e['time']
            mode           = 'buffering'
        elif e['event'] == 'PLAYING':
            bufferingTime += (e['time'] - lastTime)
            lastTime       = e['time']
            mode           = 'playing'
    
    if mode == 'playing':
        playingTime   += res['events'][-1]['time'] - lastTime
    elif mode == 'buffering':
        bufferingTime += res['events'][-1]['time'] - lastTime
    else:
        print 'WHAT THE F?'
        sys.exit()
    
    try:
        finalFractionLoaded = round(finalFractionLoaded, 3)
        bufferingTimeFrac   = round(100*float(bufferingTime)/(bufferingTime+playingTime), 1)
        bufferingTime       = round(bufferingTime/1000.0, 3)
        playingTime         = round(playingTime/1000.0, 3)
    except:
        print 'KIR'
        continue
    
    rebufferCount -= 1  #these are REbuffers, so the very first buffering should be subtracted
    
    try:
        results[bingeon][desiredQuality]
    except KeyError:
        results[bingeon][desiredQuality] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[], 'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[], 'playingTime':[]}
    finally:
        results[bingeon][desiredQuality]['timeToStartPlaying'].append(timeToStartPlaying)
        results[bingeon][desiredQuality]['initialQuality'].append(initialQuality)
        results[bingeon][desiredQuality]['endQuality'].append(endQuality)
        results[bingeon][desiredQuality]['qualityChangeCount'].append(qualityChangeCount)
        results[bingeon][desiredQuality]['rebufferCount'].append(rebufferCount)
        results[bingeon][desiredQuality]['finalFractionLoaded'].append(finalFractionLoaded)
        results[bingeon][desiredQuality]['bufferingTimeFrac'].append(bufferingTimeFrac)
        results[bingeon][desiredQuality]['bufferingTime'].append(bufferingTime)
        results[bingeon][desiredQuality]['playingTime'].append(playingTime)
        
    print '\t'.join(map(str, [file.rpartition('/')[2], network, bingeon, tether, timeToStartPlaying, desiredQuality, initialQuality, endQuality, qualityChangeCount, rebufferCount, finalFractionLoaded, bufferingTimeFrac, bufferingTime, playingTime]))
    
    
print '\n\nErrors (First 4 events are not the expected!):'
for file in errors:
    print file
    

print '\t'.join(['timeToStartPlaying', 'qualityChangeCount', 'rebufferCount', 'finalFractionLoaded', 'bufferingTimeFrac', 'bufferingTime', 'playingTime'])
for q in sorted(results['On'].keys()):
    print '\t & '.join(map(str, [q, 
                              round(numpy.average(results['On'][q]['timeToStartPlaying'])/1000.0, 2),
                              round(numpy.average(results['Off'][q]['timeToStartPlaying'])/1000.0, 2), 
                              round(numpy.average(results['On'][q]['finalFractionLoaded']), 2),
                              round(numpy.average(results['Off'][q]['finalFractionLoaded']), 2), 
                              round(numpy.average(results['On'][q]['rebufferCount']), 2),
                              round(numpy.average(results['Off'][q]['rebufferCount']), 2), 
                              round(numpy.average(results['On'][q]['bufferingTimeFrac']), 2),
                              round(numpy.average(results['Off'][q]['bufferingTimeFrac']), 2),
                              '\\ \hline' 
                              ]))
                                  
    