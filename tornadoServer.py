import os, json
import tornado.ioloop, tornado.web

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

def analyzeQoE(dir):

    for file in os.listdir(dir):

        res = json.load(open(os.path.abspath(dir) + '/' + file, 'r'))

        network             = res['network']
        tether              = res['tether']
        desiredQuality      = res['desiredQuality']
        initialQuality      = res['events'][2]['event.data']
        finalFractionLoaded = res['events'][-1]['VideoLoadedFraction']
        timeToStartPlaying  = res['events'][3]['time'] - res['events'][0]['time']
        videoID             = res['videoID']

        endQuality          = initialQuality

        rebufferCount       = 0
        qualityChangeCount  = 0

        bufferingTime       = 0
        playingTime         = 0
        lastTime            = res['events'][1]['time']
        mode                = 'playing'

        for e in res['events']:
            if e['event'] == 'QualityChange':
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

        try:
            finalFractionLoaded = round(finalFractionLoaded, 3)
            bufferingTimeFrac   = round(100*float(bufferingTime)/(bufferingTime+playingTime), 1)
            bufferingTime       = round(bufferingTime/1000.0, 3)
            playingTime         = round(playingTime/1000.0, 3)
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
            results[videoID] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[], 'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[], 'playingTime':[]}
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

        print '\t'.join(map(str, [file.rpartition('/')[2], network, 'tether? ' + tether, timeToStartPlaying, desiredQuality, initialQuality, endQuality, qualityChangeCount, rebufferCount, finalFractionLoaded, bufferingTimeFrac, bufferingTime, playingTime]))


    print '\r\n Summary:'
    print '\t & '.join(['videoID', 'initialQuality', 'endQuality', 'timeToStartPlaying', 'qualityChangeCount', 'rebufferCount', 'finalFractionLoaded', 'bufferingTimeFrac', 'bufferingTime', 'playingTime'])
    return results


class Handler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        data['ip'] = self.request.remote_ip
        # CREATE A Directory for each userID
        dirName = self.settings['resultsFolder'] + data['userID']
        print '\r\n NEW DATA', data, '\n Results in directory', dirName

        if not os.path.isdir(dirName):
            os.makedirs(dirName)

        with open(dirName+'/youtubeAPI_{}_{}_{}_{}.json'.format(data['userID'], data['network'], data['videoID'], data['testID']), 'w+') as f:
            json.dump(data, f)


    def get(self):
        args = self.request.arguments
        userID = args['userID'][0]
        result = analyzeQoE(self.settings['resultsFolder'] + str(userID))

        print '\r\n GET REQUEST FOR ',str(args)
        return self.write({'success': True, 'response': result})




resultsFolder = '/home/ubuntu/youtubePlayer_results/'
os.system('mkdir -p {}'.format(resultsFolder))

application = tornado.web.Application([(r"/", Handler),])
    
application.settings = {'resultsFolder'  : resultsFolder,
                        'debug': True,
                        }

application.listen(55556)

print '\r\n Server Running '
tornado.ioloop.IOLoop.instance().start()