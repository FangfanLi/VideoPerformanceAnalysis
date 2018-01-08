# VideoPerformanceAnalysis

Test Youtube streaming performance on your network by automative streaming Youtube video(s) and collect QOE stats.

## Three main components

Client: where the tests will be running and the network to test

Web Server: where the testPage is placed (e.g., www.testserver.com)

Analysis Server: where the analysis server runs and the QOE stats collected (e.g., analysis.com)

## Initialization

1. Deploy the webpage *testPage.html* and *youtubePlayerStats.html* on the Web Server.
2. In *testPage.html*, find the function *onSubmit()*, change the first item in variable *newUrl* to the directory where *youtubePlayerStats.html* is.
```
var newUrl = ["/the/directory/to/youtubePlayerStats.html?" ...]
```
3. In *youtubePlayerStats.html*, change the variable *ncServer* to where the Analysis Server will be running. (the analyzer server runs on port 55556)
```
var ncServer = "http://analysis.com:55556/";
```
4. Deploy *tornadoServer.py* on the Analysis Server and in the script, change the variable *resultsFolder* to where you want the results to be kept.
```
resultsFolder = '/home/ubuntu/youtubePlayer_results/'
```
5. In *automated_youtube_api.py*, update the driver path, and you might need to download the driver.
```python
...
    driver = webdriver.Chrome('/the/path/to/ChomeDriver/chromedriver',chrome_options=chromeOptions)
elif browser == 'Firefox':
    driver = webdriver.Firefox(executable_path='/the/path/to/FirefoxDriver/geckodriver')
...
```
In *runOne()* method, update the url to where the testPage is hosted.
```
url = 'http://www.testserver.com/youtubePlayerStats.html?tether={}&stoptime={}&network={}&quality={}&videoID={}'.format(tether, stoptime, network, quality,videoID)
```

## Run one set of tests

1. On the Analysis Server, run *tornadoServer.py* by typing 
```
sudo python tornadoServer.py
```
2. On the client machine, run *automated_youtube_api.py*
```
sudo python automated_youtube_api.py WiFi NO Firefox
```
Where the first parameter specifies which network is being tested ('WiFi'), the second parameter is whether tethered ('NO'), the third parameter is which browser to use for testing ('Firefox'). The program prints out the meta data for each test it performs: testID, specified resolution, network, userID, videoID.
3. Once the experiment finished, on the Analysis Server, run *analyzeByVideoID.py* by:
```
python analyzeByVideoID.py /home/ubuntu/youtubePlayer_results/userID
```
Where userID is from the test you just performed, each directory contains all the test results for one experiments (i.e., one userID) on the server.
4. The output should look like this:
```
videoID	 & initialQuality	 & endQuality	 & timeToStartPlaying	 & qualityChangeCount	 & rebufferCount	 & finalFractionLoaded	 & bufferingTimeFrac	 & bufferingTime	 & playingTime
```
```
RgKAFK5djSk	 & {u'hd1080': 0.8, u'hd720': 0.2}	 & {u'hd1080': 1.0}	 & 1.78	 & 1.2	 & 0.2	 & 51.0%	 & 3.22%	 & 1.98	 & 59.8
```
```
kJQP7kiw5Fk	 & {u'medium': 0.4, u'hd720': 0.6}	 & {u'hd1080': 0.2, u'hd720': 0.8}	 & 1.74	 & 2.8	 & 0.8	 & 36.0%	 & 4.04%	 & 2.51 & 59.26
```


## Interpret the result

There are nine QOE stats collected for each experiment, namely:

initialQuality, endQuality: each key in the list shows the video quality at the start/end of the streaming, the corresponding value is the percentage that this quality appeared (e.g. 'hd720' :0.2 in initialQuality means that the video starts with hd720 20% of the time).

The rest of the stats should be self explanatory by their names.

Let's take the example output above, where the top two videos are tested, each for 5 times on a WIFI network.

The result for videoID *'RgKAFK5djSk'* shows that the video starts with 
*hd1080* 80% and *hd720* 20% of the time; the video always end in *hd1080* quality; time before the video starts averages to *1.78* seconds; on average the quality changes *1.2* times during the test; on average the video buffers *0.2* times; at the end of the test period (60s), on average *51%* of the video is already loaded; buffering time only counts for *3%* of the streaming period; buffering time on average is *1.98* seconds.

## Tunable parameters

In *automated_youtube_api.py*, there are few variables can be set for different experiments.

```
videoIDs = getTopYoutubeVideoIDs(n)
```
*getTopYoutubeVideoIDs* returns the videoIDs of the top *n* most-viewed youtube videos according to https://en.wikipedia.org/wiki/List_of_most-viewed_YouTube_videos.
```python
doDumps = False
stoptime = '10'
rounds = 5
```
When *doDumps* is set to True, the script will do a tcpdump for each test in the */tcpdumps/* subdirectory for each userID.

*stoptime* sets for how long each video should be played for testing.

*rounds* sets for how many times each video should be played (tested).




