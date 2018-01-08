'''
This script gets most viewed videoIDs from Wikipedia by parsing

https://en.wikipedia.org/wiki/List_of_most-viewed_YouTube_videos
'''


from urllib2 import urlopen
from BeautifulSoup import BeautifulSoup

url = 'https://en.wikipedia.org/wiki/List_of_most-viewed_YouTube_videos'
soup = BeautifulSoup(urlopen(url).read())

# print soup

# table = soup.find(lambda tag: tag.name=='table' and tag.has_key('class') and tag['class']=="wikitable sortable jquery-tablesorter")
#
# rows = table.findAll(lambda tag: tag.name=='tr')
sortTable = soup.find( "table", {"class":"wikitable sortable"})

# reflist columns references-column-width

refTable = soup.find("div", {"class":"reflist columns references-column-width"})

rows=list()

allVideo = sortTable.findAll("tr")

allIDs = []

for ind in xrange(1,51):
    video = allVideo[ind]
    td = video.findAll("td")[1]
    # print '\r\n td', td
    refID = td.find('sup').find('a').get('href').split('#')[1]
    # print '\r\n refID',refID
    allIDs.append(refID)


print len(allIDs)


# print '\r\n', refTable

allYoutubeIDs = []
for ref in refTable.findAll("li"):
    # print '\r\n ~',ref.get('id'), ref.get('id') == refID
    if ref.get('id') in allIDs:
        link = ref.find('a', {"class": "external text"}).get('href')
        youtubeID = link.split('=')[1]
        # print '\r\n~', link
        allYoutubeIDs.append(youtubeID)

print allYoutubeIDs

print len(allYoutubeIDs)
