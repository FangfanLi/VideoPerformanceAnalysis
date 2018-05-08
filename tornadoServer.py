import os, json
import tornado.ioloop, tornado.web

import sys, json, numpy,os, time, subprocess
import re
import ast

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
    results = {}

    for file in os.listdir(dir):

        res = json.load(open(os.path.abspath(dir) + '/' + file, 'r'))
        network             = res['network']
        tether              = res['tether']
        videoID             = res['videoID']
        timeToStartPlaying  = res['events'][1]['time'] - res['events'][0]['time']
        entireTime          = round((res['events'][-1]['time'] - res['events'][0]['time'])/1000.0, 3)

        if 'netflix' in file:
            print 'netflix found in file'
            print res['events']
            # finding initial quality
            counter = 0
            initialQuality = ''
            # second event is the actual playing, zero is unstarted, one is buffer
            first_event = res['events'][2]
            print first_event
            print '--'
            clean_dict = {k.replace(' ', ''): v for k, v in first_event.items()}
            print clean_dict
            print '==='
            try:
                initialQuality = re.findall(r'x.*',clean_dict['Playingbitrate(a/v)'])[0].replace('x','').replace(')','').strip()
            except Exception as exp:
                initialQuality = '240'
                print ' exception '
                pass 

            endQuality          = initialQuality

            print initialQuality, ' this is our initial quality'
            print '--------'
            video_duration      = re.findall(r'duration=[0-9]+\.[0-9]+',res['events'][-1]['VideoDiag'])[0].replace('duration=','')
            finalBufferLoaded = re.findall(r'videoBuffered=[0-9]+\.[0-9]+',res['events'][-1]['VideoDiag'])[0].replace('videoBuffered=','')
            finalFractionLoaded = float(finalBufferLoaded)/float(video_duration)

            timeToStartPlaying  = res['events'][1]['time'] - res['events'][0]['time']
            lastQualityStartsAT    = res['events'][2]['time']

            rebufferCount       = 0
            qualityChangeCount  = 0
            # The fist event is always unstarted, consider the start of the buffering as the start of the analysis, which is res['events'][0]
            initialTime = res['events'][0]['time']

            bufferingTime       = 0
            playingTime         = 0
            lastTime            = res['events'][0]['time']
            mode                = 'playing'

            diffQualitiesPeriod = {}

            # Buffering events list, which contains all qualities and buffering events, e.g.,
            # event : timestamp (relative to the very first event)
            # ['Start buffering', u'Quality changes to medium after buffering for 1.136 seconds', 'Video buffered for 2.495 seconds',
            # u'Quality changes to large after playing for 3.766 seconds', '4.516 seconds later after the previous quality change, buffering starts',
            # 'Video buffered for 1.841 seconds']
            prev_player_state = ''
            bEvents = []
            for e in res['events']:
                print 'event is ', str(e)
                print '---------\n'
                clean_d = {k.replace(' ', ''): v for k, v in e.items()}
                print clean_d
                player_state = clean_d['changeevent']
                curr_time = str(clean_d['time'])

                if player_state =='QualityChange':
                    # Calculate previous quality time
                    etime = e['time'] - lastQualityStartsAT
                    lastQualityStartsAT = e['time']
                    if not diffQualitiesPeriod.has_key(endQuality):
                        diffQualitiesPeriod[endQuality] = 0
                    diffQualitiesPeriod[endQuality] += round(etime/1000.0, 3)
                    endQuality     = quality = re.findall(r'x.*',clean_d['Playingbitrate(a/v)'])[0].replace('x','').replace(')','').strip()
                    qualityChangeCount += 1
                    bEvents.append('Quality change : ' + endQuality + ' : ' + str(round((e['time'] - initialTime)/1000.0, 3)))

                elif player_state == 'Waiting for decoder':
                    rebufferCount += 1
                    playingTime   += (e['time'] - lastTime)
                    lastTime       = e['time']
                    mode           = 'buffering'
                    bEvents.append('Buffering : ' + str(round((e['time'] - initialTime)/1000.0, 3)))

                elif player_state == 'Playing':
                    bufferingTime += (e['time'] - lastTime)
                    bEvents.append('Playing : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
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
                results[videoID] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[],
                                    'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[],
                                    'playingTime':[], 'multiTestsQualities':[], 'bEvents':[]}
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
                results[videoID]['bEvents'].append(bEvents)
        if 'vimeo' in file:
            print 'vimeo bro'
            print res['events']
            print ' //////////////////////// ^^^^^^^ EVENTS ^^^^^^^ ///////////////////'

            # change the res because playing and change quality need to be exchanged
            quality_event = res['events'][3]
            playing_event = res['events'][2]
            res['events'][2] = quality_event
            res['events'][3] = playing_event
            # res['events'][2]['time'] = res['events'][3]['time']
            res['events'][3]['time'] = res['events'][2]['time']
            print res
            print ' new res ^^^^^'


            # Sanity check, first event should be 'UNSTARTED', second event should be 'BUFFERING', third event should be 'QualityChange'
            # Otherwise, ignore this data point
            if res['events'][0]['event'] != 'UNSTARTED' or res['events'][1]['event'] != 'BUFFERING' or res['events'][2]['event'] != 'QualityChange':
                continue
            desiredQuality      = res['desiredQuality']
            initialQuality      = res['events'][2]['event.data']
            finalFractionLoaded = res['events'][-1]['event.data']['percent']
            timeToStartPlaying  = res['events'][3]['time'] - res['events'][0]['time']
            lastQualityStartsAT    = res['events'][3]['time']
            entireTime          = round((res['events'][-1]['time'] - res['events'][3]['time'])/1000.0, 3)

            endQuality          = initialQuality
            print initialQuality, ' init quality'
            rebufferCount       = 0
            qualityChangeCount  = 0
            # The fist event is always unstarted, consider the start of the buffering as the start of the analysis, which is res['events'][1]
            initialTime = res['events'][1]['time']

            bufferingTime       = 0
            playingTime         = 0
            lastTime            = res['events'][1]['time']
            mode                = 'playing'

            diffQualitiesPeriod = {}

            # Buffering events list, which contains all qualities and buffering events, e.g.,
            # event : timestamp (relative to the very first event)
            # ['Start buffering', u'Quality changes to medium after buffering for 1.136 seconds', 'Video buffered for 2.495 seconds',
            # u'Quality changes to large after playing for 3.766 seconds', '4.516 seconds later after the previous quality change, buffering starts',
            # 'Video buffered for 1.841 seconds']

            bEvents = []
            prev_event_was_buffer = False
            for e in res['events']:
                print e
                print '================ / / / / / / / -=============='
                if e['event'] == 'QualityChange':
                    prev_event_was_buffer = False
                    # Calculate previous quality time
                    etime = e['time'] - lastQualityStartsAT
                    lastQualityStartsAT = e['time']
                    if not diffQualitiesPeriod.has_key(endQuality):
                        diffQualitiesPeriod[endQuality] = 0
                    print diffQualitiesPeriod
                    print endQuality
                    diffQualitiesPeriod[endQuality] += round(etime/1000.0, 3)
                    endQuality     = e['event.data']
                    qualityChangeCount += 1
                    bEvents.append('Quality change : ' + endQuality + ' : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
                elif e['event'] == 'BUFFERING':
                    if prev_event_was_buffer == False:
                        rebufferCount += 1
                        playingTime   += (e['time'] - lastTime)
                        lastTime       = e['time']
                        mode           = 'buffering'
                        bEvents.append('Buffering : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
                        prev_event_was_buffer = True
                    else:
                        print ' just did a buffer son'
                elif e['event'] == 'PLAYING':
                    prev_event_was_buffer = False
                    bufferingTime += (e['time'] - lastTime)
                    bEvents.append('Playing : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
                    lastTime       = e['time']
                    mode           = 'playing'
                else:
                    prev_event_was_buffer = False
            print '.........'
            print bEvents
            print '.........'
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
                results[videoID] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[],
                                    'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[],
                                    'playingTime':[], 'multiTestsQualities':[], 'bEvents':[]}
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
                results[videoID]['bEvents'].append(bEvents)
                print results[videoID]['rebufferCount']
        if 'youtube' in file:
            # Sanity check, first event should be 'UNSTARTED', second event should be 'BUFFERING', third event should be 'QualityChange'
            # Otherwise, ignore this data point
            if res['events'][0]['event'] != 'UNSTARTED' or res['events'][1]['event'] != 'BUFFERING' or res['events'][2]['event'] != 'QualityChange':
                continue

            desiredQuality      = res['desiredQuality']
            initialQuality      = res['events'][2]['event.data']
            finalFractionLoaded = res['events'][-1]['VideoLoadedFraction']
            timeToStartPlaying  = res['events'][3]['time'] - res['events'][0]['time']
            lastQualityStartsAT    = res['events'][2]['time']
            entireTime          = round((res['events'][-1]['time'] - res['events'][2]['time'])/1000.0, 3)

            endQuality          = initialQuality

            rebufferCount       = 0
            qualityChangeCount  = 0
            # The fist event is always unstarted, consider the start of the buffering as the start of the analysis, which is res['events'][1]
            initialTime = res['events'][1]['time']

            bufferingTime       = 0
            playingTime         = 0
            lastTime            = res['events'][1]['time']
            mode                = 'playing'

            diffQualitiesPeriod = {}

            # Buffering events list, which contains all qualities and buffering events, e.g.,
            # event : timestamp (relative to the very first event)
            # ['Start buffering', u'Quality changes to medium after buffering for 1.136 seconds', 'Video buffered for 2.495 seconds',
            # u'Quality changes to large after playing for 3.766 seconds', '4.516 seconds later after the previous quality change, buffering starts',
            # 'Video buffered for 1.841 seconds']

            bEvents = []

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
                    bEvents.append('Quality change : ' + endQuality + ' : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
                elif e['event'] == 'BUFFERING':
                    rebufferCount += 1
                    playingTime   += (e['time'] - lastTime)
                    lastTime       = e['time']
                    mode           = 'buffering'
                    bEvents.append('Buffering : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
                elif e['event'] == 'PLAYING':
                    bufferingTime += (e['time'] - lastTime)
                    bEvents.append('Playing : ' + str(round((e['time'] - initialTime)/1000.0, 3)))
                    lastTime       = e['time']
                    mode           = 'playing'

            if mode == 'playing':
                playingTime   += res['events'][-1]['time'] - lastTime
                print playingTime, ' playingTime'
            elif mode == 'buffering':
                bufferingTime += res['events'][-1]['time'] - lastTime
            else:
                print 'WHAT THE F?'
                sys.exit()
            print '.........'
            print bEvents
            print '.........'
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
                results[videoID] = {'timeToStartPlaying':[], 'initialQuality':[], 'endQuality':[], 'qualityChangeCount':[],
                                    'rebufferCount':[], 'finalFractionLoaded':[], 'bufferingTimeFrac':[], 'bufferingTime':[],
                                    'playingTime':[], 'multiTestsQualities':[], 'bEvents':[]}
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
                results[videoID]['bEvents'].append(bEvents)

        # move the result directory to a timstamped subdirectory
        incomingDate = time.strftime("%Y-%m-%d", time.gmtime())
        resultDir= dir.rpartition('/')[0]
        testID = dir.rsplit('/')[-1]
        timestampedDir = resultDir + '/' + incomingDate
        newdir = timestampedDir + '/' + testID
        if not os.path.isdir(timestampedDir):
            os.makedirs(timestampedDir)
        subprocess.call('mv ' + dir + ' ' + newdir, stdout=subprocess.PIPE, shell=True)

    return results


class Handler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        data['ip'] = self.request.remote_ip
        print 'post request is'
        print self.request
        # CREATE A Directory for each userID
        dirName = self.settings['resultsFolder'] + data['userID']
        print '\r\n NEW DATA', data, '\n Results in directory', dirName

        if not os.path.isdir(dirName):
            os.makedirs(dirName)

        print 'content provider is ', data['contentprovider']
        if data['contentprovider'] == 'youtube':
            with open(dirName+'/youtubeAPI_{}_{}_{}_{}.json'.format(data['userID'], data['network'], data['videoID'], data['testID']), 'w+') as f:
                json.dump(data, f)
        if data['contentprovider'] == 'netflix':
            with open(dirName+'/netflixAPI_{}_{}_{}_{}.json'.format(data['userID'], data['network'], data['videoID'], data['testID']), 'w+') as f:
                json.dump(data, f)
        if data['contentprovider'] == 'vimeo':
            with open(dirName+'/vimeoAPI_{}_{}_{}_{}.json'.format(data['userID'], data['network'], data['videoID'], data['testID']), 'w+') as f:
                json.dump(data, f)


    def get(self):
        args = self.request.arguments
        userID = args['userID'][0]
        result = analyzeQoE(self.settings['resultsFolder'] + str(userID))

        print '\r\n GET REQUEST FOR ',str(args)
        return self.write({'success': True, 'response': result})




# resultsFolder = '/Users/arian/Desktop/WeHe/Player_results/'
resultsFolder = '/Users/arian/Desktop/WeHe/VideoPerformanceAnalysis/Results/'
os.system('mkdir -p {}'.format(resultsFolder))

application = tornado.web.Application([(r"/", Handler),])
    
application.settings = {'resultsFolder'  : resultsFolder,
                        'debug': True,
                        }

application.listen(55556)

print '\r\n Server Running '
tornado.ioloop.IOLoop.instance().start()