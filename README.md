# VideoPerformanceAnalysis

Test Youtube streaming performance on your network by automative streaming Youtube video(s) and collect QOE stats.

## Three main components

Client: where the tests will be running and the network to test

Web Server: where the testPage is placed (e.g., testserver.com)

Analysis Server: where the analysis server runs and the QOE stats collected (e.g., analysis.com)

## Two ways to run tests

1. Use the tool as it is configured now, it now uses a webpage hosted by myself and an analysis server that runs on an EC2 machine.

2. Deploy the tool on your own tool, host the webpage and analysis server in your own frastracture.

I would suggest trying out the tool for a bit using the configuration as it is, and I guess you want to eventually deploy the tool to your own servers thus have more control over it.

### 1. Use the tool as it is

#### Initialization

You probably need to install several python packages (e.g. selenium), and download the webdrivers for [Firefox](https://github.com/mozilla/geckodriver/releases) and [Chrome](https://sites.google.com/a/chromium.org/chromedriver/downloads).

In *automated\_youtube\_api.py*, find the two lines below, change the paths to the where you put the drivers on your machine.

```python
driver = webdriver.Chrome('/path/to/chromedriver')
...
driver = webdriver.Firefox(executable_path='/path/to/geckodriver')
```

#### a. Run one set of tests

1. On the client machine, run *automated_youtube_api.py*
```python
python automated_youtube_api.py WiFi NO Firefox
```
Where the first parameter specifies which network is being tested ('WiFi'), the second parameter is whether tethered ('NO'), the third parameter is which browser to use for testing ('Firefox'). The program prints out the meta data for each test it performs: testID, specified resolution, network, userID, videoID.

2. When the experiment is running, the script opens up the browser and loads video repeatively.

3. The output should look something like this:
```
videoID	 & initialQuality	 & endQuality	 & timeToStartPlaying	 & qualityChangeCount	 & rebufferCount	 & finalFractionLoaded	 & bufferingTimeFrac	 & bufferingTime	 & playingTime
```
```
kJQP7kiw5Fk	 & {u'hd1080': 0.7, u'medium': 0.3}	 & {u'hd1080': 1.0}	 & 1.13	 & 1.3	 & 0.0	 & 25.0%	 & 3.83%	 & 1.2	 & 30.0
```

#### b. Interpret the result

There are nine QOE stats collected for each experiment, namely:

initialQuality, endQuality: each key in the list shows the video quality at the start/end of the streaming, the corresponding value is the percentage that this quality appeared (e.g. 'hd720' :0.2 in initialQuality means that the video starts with hd720 20% of the time).

The rest of the stats should be self explanatory by their names.

Let's take the example output above, where the top two videos are tested, each for 5 times on a WIFI network.

The result for videoID *'kJQP7kiw5Fk'* shows that the video starts with 
*hd1080* 70% and *medium* 30% of the time; the video always end in *hd1080* quality; time before the video starts averages to *1.13* seconds; on average the quality changes *1.3* times during the test; on average the video buffers *0.0* times; at the end of the test period (30s), on average *25%* of the video is already loaded; buffering time only counts for *3.83%* of the streaming period; buffering time on average is *1.2* seconds.

#### c. Tunable parameters

In *automated\_youtube\_api.py*, there are few variables can be set for different experiments.

```
videoIDs = getTopYoutubeVideoIDs(n)
```
*getTopYoutubeVideoIDs* returns the videoIDs of the top *n* most-viewed youtube videos according to [this page](https://en.wikipedia.org/wiki/List_of_most-viewed_YouTube_videos).
```python
doDumps = False
stoptime = '10'
rounds = 5
```
When *doDumps* is set to True, the script will do a tcpdump for each test in the */tcpdumps/* subdirectory for each userID. (* Note you will need sudo when this parameter is set to True)

*stoptime* sets how long each video should be played for testing.

*rounds* sets how many times each video should be played (tested).


### 2. Deploy the tool on your own infrastructure

#### a. Initialization

1. Deploy the webpage *testPage.html* and *youtubePlayerStats.html* on the Web Server.
2. In *testPage.html*, find the function *onSubmit()*, change the first item in variable *newUrl* to the directory where *youtubePlayerStats.html* is.
```
var newUrl = ["/the/directory/to/youtubePlayerStats.html?" ...]
```
3. In *youtubePlayerStats.html*, change the variable *ncServer* to where the Analysis Server will be running. (the analyzer server runs on port 55556)
```
var ncServer = "http://analysis.com:55556/";
```
4. Deploy *tornadoServer.py* on the Analysis Server and in the script, change the variable *resultsFolder* to where you want the results to be kept, and start it with *python tornadoServer.py*.
```
resultsFolder = '/home/ubuntu/youtubePlayer_results/'
```
5. In *automated\_youtube\_api.py*, find *runOne()* method, update the url to where the testPage is hosted.
```
url = 'http://www.testserver.com/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}'.format(tether, stoptime, network, quality,videoID)
```






