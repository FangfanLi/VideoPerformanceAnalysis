import sys, json, numpy,os

errors  = []
results = {}

'''
The results should be grouped by each set of tests (with unique userID)
Input: the directory which contains the results of the same userID

Print Out (grouped by videoID):

initial Quality
end Quality
time To Start Playing (averaged)
quality Change Count (averaged)
rebuffer Count (averaged)
final Fraction Loaded (averaged)
bufferingTime Frac (averaged)
buffering Time (averaged)
playing Time (averaged)
'''


# Input: a list of qualities
# Output: a dictionary of qualities and their percentage in the Input
# Example: ['hd1080', 'hd720'] ---> {'hd1080':0.5, 'hd720':0.5}

def getQualityPercentage(qualities):
    rQualities = {}
    for quality in qualities:
        if rQualities.has_key(quality):
            rQualities[quality] += 1
        else:
            rQualities[quality] = 1

    for quality in rQualities:
        rQualities[quality] = float(rQualities[quality])/float(len(qualities))

    return rQualities

def getQualityPeriod(multiTestsQualities):
    rQualities = {}
    numTests = len(multiTestsQualities)
    for singleTestQualities in multiTestsQualities:
        for quality in singleTestQualities.keys():
            if not rQualities.has_key(quality):
                rQualities[quality] = 0
            rQualities[quality] += singleTestQualities[quality]

    for quality in rQualities:
        rQualities[quality] = round(rQualities[quality]/float(numTests),2)

    return rQualities


def main():

    try:
        dir = sys.argv[1]
    except:
        print '\r\n Pleas provide input: [the directory where the results are]'
        sys.exit(-1)

    for file in os.listdir(dir):

        res = json.load(open(os.path.abspath(dir) + '/' + file, 'r'))

        # Sanity check, first event should be 'UNSTARTED', second event should be 'BUFFERING', third event should be 'QualityChange'
        # Otherwise, ignore this data point
        if res['events'][0]['event'] != 'UNSTARTED' or res['events'][1]['event'] != 'BUFFERING' or res['events'][2]['event'] != 'QualityChange':
            continue

        network             = res['network']
        tether              = res['tether']
        desiredQuality      = res['desiredQuality']
        initialQuality      = res['events'][2]['event.data']
        finalFractionLoaded = res['events'][-1]['VideoLoadedFraction']
        timeToStartPlaying  = res['events'][3]['time'] - res['events'][0]['time']
        videoID             = res['videoID']
        lastQualityStartsAT    = res['events'][2]['time']
        entireTime          = round((res['events'][-1]['time'] - res['events'][2]['time'])/1000.0, 3)

        endQuality          = initialQuality

        rebufferCount       = 0
        qualityChangeCount  = 0

        bufferingTime       = 0
        playingTime         = 0
        lastTime            = res['events'][1]['time']
        mode                = 'playing'

        diffQualitiesPeriod = {}

        for e in res['events']:
            if e['event'] == 'QualityChange':
                # Calculate previous quality time
                etime = e['time'] - lastQualityStartsAT
                lastQualityStartsAT = e['time']
                if not diffQualitiesPeriod.has_key(endQuality):
                    diffQualitiesPeriod[endQuality] = 0
                diffQualitiesPeriod[endQuality] += round(etime/1000.0, 3)
                endQuality     = e['event.data']
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

        etime = res['events'][-1]['time'] - lastQualityStartsAT
        if not diffQualitiesPeriod.has_key(endQuality):
            diffQualitiesPeriod[endQuality] = 0
        diffQualitiesPeriod[endQuality] += round(etime / 1000.0, 3)

        try:
            finalFractionLoaded = round(finalFractionLoaded, 3)
            bufferingTimeFrac   = round(100*float(bufferingTime)/(bufferingTime+playingTime), 1)
            bufferingTime       = round(bufferingTime/1000.0, 3)
            playingTime         = round(playingTime/1000.0, 3)
            for quality in diffQualitiesPeriod.keys():
                diffQualitiesPeriod[quality] = round(diffQualitiesPeriod[quality]/entireTime,2)

        except:
            print 'EXCEPTION in calculating this result', file,' Skipping'
            continue

        # these are REbuffers, so the very first buffering should be subtracted
        # Sometimes there is no initial buffering event, there is no need to minus one
        if rebufferCount > 0:
            rebufferCount -= 1

        # ADD the results together
        try:
            results[videoID]
        except KeyError:
            results[videoID] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[], 'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[], 'playingTime':[], 'multiTestsQualities':[]}
        finally:
            results[videoID]['timeToStartPlaying'].append(timeToStartPlaying)
            results[videoID]['initialQuality'].append(initialQuality)
            results[videoID]['endQuality'].append(endQuality)
            results[videoID]['qualityChangeCount'].append(qualityChangeCount)
            results[videoID]['rebufferCount'].append(rebufferCount)
            results[videoID]['finalFractionLoaded'].append(finalFractionLoaded)
            results[videoID]['bufferingTimeFrac'].append(bufferingTimeFrac)
            results[videoID]['bufferingTime'].append(bufferingTime)
            results[videoID]['playingTime'].append(playingTime)
            results[videoID]['multiTestsQualities'].append(diffQualitiesPeriod)

        print '\t'.join(map(str, [file.rpartition('/')[2], network, 'tether? ' + tether, timeToStartPlaying, desiredQuality, initialQuality, endQuality, qualityChangeCount, rebufferCount, finalFractionLoaded, bufferingTimeFrac, bufferingTime, playingTime, diffQualitiesPeriod]))


    print '\r\n Summary:'
    print '\t & '.join(['videoID', 'initialQuality', 'endQuality', 'periodInDiffQualities', 'timeToStartPlaying', 'qualityChangeCount', 'rebufferCount', 'finalFractionLoaded', 'bufferingTimeFrac', 'bufferingTime', 'playingTime'])
    for q in sorted(results.keys()):
        iQualities = getQualityPercentage(results[q]['initialQuality'])
        eQualities = getQualityPercentage(results[q]['endQuality'])
        dQualities = getQualityPeriod(results[q]['multiTestsQualities'])


        print '\t & '.join(map(str, [q, iQualities, eQualities, dQualities,
                                 round(numpy.average(results[q]['timeToStartPlaying'])/1000.0, 2),
                                 round(numpy.average(results[q]['qualityChangeCount']), 2),
                                 round(numpy.average(results[q]['rebufferCount']), 2),
                                 str(round(numpy.average(results[q]['finalFractionLoaded']), 2) * 100) + '%',
                                 str(round(numpy.average(results[q]['bufferingTimeFrac']), 2)) + '%',
                                 round(numpy.average(results[q]['bufferingTime']), 2),
                                 round(numpy.average(results[q]['playingTime']), 2)
                                 ]))

if __name__ == "__main__":
    main()