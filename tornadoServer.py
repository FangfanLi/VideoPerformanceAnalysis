import os, json
import tornado.ioloop, tornado.web

class Handler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        data['ip'] = self.request.remote_ip
        print data, '\n'
        with open('/home/ubuntu/youtubePlayer_results/youtubeAPI_{}_{}.json'.format(data['userID'], data['testID']), 'w+') as f:
            json.dump(data, f)

resultsFolder = '/home/ubuntu/youtubePlayer_results/'
os.system('mkdir -p {}'.format(resultsFolder))

application = tornado.web.Application([(r"/", Handler),])
    
application.settings = {'resultsFolder'  : resultsFolder,
                        'debug': True,
                        }

application.listen(55556)

tornado.ioloop.IOLoop.instance().start()
