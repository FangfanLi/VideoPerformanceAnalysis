import sys, json, numpy

errors  = []
results = {}

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
        results[desiredQuality]
    except KeyError:
        results[desiredQuality] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[], 'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[], 'playingTime':[]}
    finally:
        results[desiredQuality]['timeToStartPlaying'].append(timeToStartPlaying)
        results[desiredQuality]['initialQuality'].append(initialQuality)
        results[desiredQuality]['endQuality'].append(endQuality)
        results[desiredQuality]['qualityChangeCount'].append(qualityChangeCount)
        results[desiredQuality]['rebufferCount'].append(rebufferCount)
        results[desiredQuality]['finalFractionLoaded'].append(finalFractionLoaded)
        results[desiredQuality]['bufferingTimeFrac'].append(bufferingTimeFrac)
        results[desiredQuality]['bufferingTime'].append(bufferingTime)
        results[desiredQuality]['playingTime'].append(playingTime)

    print '\t'.join(map(str, [file.rpartition('/')[2], network, 'tether? ' + tether, timeToStartPlaying, desiredQuality, initialQuality, endQuality, qualityChangeCount, rebufferCount, finalFractionLoaded, bufferingTimeFrac, bufferingTime, playingTime]))


print '\n\nErrors (First 4 events are not the expected!):'
for file in errors:
    print file


print '\n\n Summary:'
print '\t '.join(['timeToStartPlaying', 'qualityChangeCount', 'rebufferCount', 'finalFractionLoaded', 'bufferingTimeFrac', 'bufferingTime', 'playingTime'])
for q in sorted(results.keys()):
    print '\t\t & '.join(map(str, [q,
                                 round(numpy.average(results[q]['timeToStartPlaying'])/1000.0, 2),
                                 round(numpy.average(results[q]['qualityChangeCount']), 2),
                                 round(numpy.average(results[q]['rebufferCount']), 2),
                                 str(round(numpy.average(results[q]['finalFractionLoaded']), 2) * 100) + '%',
                                 str(round(numpy.average(results[q]['bufferingTimeFrac']), 2)) + '%',
                                 round(numpy.average(results[q]['bufferingTime']), 2),
                                 round(numpy.average(results[q]['playingTime']), 2),
                                 '\\ \hline'
                                 ]))