import os, json
import tornado.ioloop, tornado.web

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

resultsFolder = '/home/ubuntu/youtubePlayer_results/'
os.system('mkdir -p {}'.format(resultsFolder))

application = tornado.web.Application([(r"/", Handler),])
    
application.settings = {'resultsFolder'  : resultsFolder,
                        'debug': True,
                        }

application.listen(55556)

print '\r\n Server Running '
tornado.ioloop.IOLoop.instance().start()