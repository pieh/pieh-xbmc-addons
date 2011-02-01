import xml.dom.minidom
from threading import Thread
import urllib, os.path, xbmc, re, htmlentitydefs, time

CWD = os.getcwd()
if CWD[-1] == ';': CWD = CWD[0:-1]
if CWD[-1] != '\\': CWD = CWD + '\\'

DATA_PATH = xbmc.translatePath( "special://profile/addon_data/script.rssclient/")
if not os.path.exists(DATA_PATH): os.makedirs(DATA_PATH)

def log(txt):
    print 'LOG script.rssclient: %s' % txt

def checkDir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        
def getCacheThumbName(url, multiimagepath):
    thumb = xbmc.getCacheThumbName(url)
           
    if 'jpg' in url:
        thumb = thumb.replace('.tbn', '.jpg')
    elif 'png' in url:
        thumb = thumb.replace('.tbn', '.png')
    elif 'gif' in url:
        thumb = thumb.replace('.tbn', '.gif')           
    
    tpath = os.path.join(multiimagepath, thumb)
    return tpath

def download(src,dst):
    #first cache
    
    tmpname = xbmc.translatePath('special://temp/%s' % xbmc.getCacheThumbName(src))
    
    if os.path.exists(tmpname):
        os.remove(tmpname)
    
    urllib.urlretrieve(src, filename = tmpname)
    os.rename(tmpname, dst)

class ImageCacher(Thread):
    def __init__(self):
        
        Thread.__init__(self)
        self.queue = []
        self.isRunning = False
        self.keepRunning = True
        self.setDaemon(True)
    
    def alarmExit(self):
        self.keepRunning = False
        log('Force Exit')
    
    def enqueue(self, item):
        if len(item.imageURLS) > 0:
            self.queue.append(item)
           
            if not self.isRunning:
                self.isRunning = True
                self.start()
    
    def run(self):
        self.isRunning = True
        while self.keepRunning and len(self.queue) > 0:
            try:
                item = self.queue[0]
                for url in item.imageURLS:
                    tpath = getCacheThumbName(url, item.multiimagepath)
                    
                    if not os.path.exists(tpath):
                        download(url, tpath)
                    
            except:
                print 'SOME ERROR LOL'

            del self.queue[0]
            
        self.isRunning = False
        
class RSSItem:
    def __init__(self):
        self.description = ''
        self.channel = None
        self.title = ''
        self.link = ''
        self.date = 'N/A'
        self.date_int = 0
        self.image = []
        self.imageURLS = []
        self.video = ''
        self.read = False
        self.multiimagepath = ''
        
class RSSChannel:
    def __init__(self):
        self.items = []
        self.title = 'channel title'
        self.link = 'channel link'
        self.description = 'channel description'
        self.read = False
        self.unread_count = 0
        
class RSSSource:
    def __init__(self):
        self.channels = []
        self.updateinterval = 30
        self.url = ''
        self.lastupdate = 0

class RSSSet:
    def __init__(self):
        self.id = '0'
        self.sources = []


        
        
class TimeZoneHandler:
    def __init__(self):
        self.zones = ['CET', 'ACDT', 'ACST', 'ACT', 'ADT', 'AEDT', 'AEST', 'AFT', 'AKDT', 'AKST', 'AMST', 'AMT', 'ART', 'AST', 'AWDT', 'AWST', 'AZOST', 'AZT', 'BDT', 'BIOT', 'BIT', 'BOT', 'BRT', 'BST', 'BTT', 'CAT', 'CCT', 'CDT', 'CEDT', 'CEST', 'CET', 'CHAST', 'CIST', 'CKT', 'CLST', 'CLT', 'COST', 'COT', 'CST', 'CVT', 'CXT', 'ChST', 'DFT', 'EAST', 'EAT', 'ECT', 'EDT', 'EEDT', 'EEST', 'EET', 'EST', 'FJT', 'FKST', 'GALT', 'GET', 'GFT', 'GILT', 'GIT', 'GST', 'GYT', 'HADT', 'HAST', 'HKT', 'HMT', 'HST', 'IRKT', 'IRST', 'IST', 'JST', 'KRAT', 'KST', 'LHST', 'LINT', 'MAGT', 'MDT', 'MIT', 'MSD', 'MSK', 'MST', 'MUT', 'NDT', 'NFT', 'NPT', 'NST', 'NT', 'OMST', 'PDT', 'PETT', 'PHOT', 'PKT', 'PST', 'RET', 'SAMT', 'SAST', 'SBT', 'SCT', 'SLT', 'SST', 'TAHT', 'THA', 'UTC', 'UYST', 'UYT', 'VET', 'VLAT', 'WAT', 'WEDT', 'WEST', 'WET', 'YAKT', 'YEKT']
        self.zonesoffset =[1, 10.5, 9.5, 8, -3, 11, 10, 4.5, -8, -9, 5, 4, -3, 3, 9, 8, -1, 4, 8, 6, -12, -4, -3, 1, 6, 2, 6.5, -5, 2, 2, 1, 12.75, -8, -10, -3, -4, -4, -5, -6, -1, 7, 10, 1, -6, 3, -4, -4, 3, 3, 2, -5, 12, -4, -6, 4, -3, 12, -9, -2, -4, -9, -10, 8, 5, -10, 8, 3.5, 1, 9, 7, 9, 10.5, 14, 11, -6, -9.5, 4, 3, -7, 4, -2.5, 11.5, 5.75, -3.5, -3.5, 6, -7, 12, 13, 5, -8, 4, 4, 2, 11, 4, 5.5, 8, -10, 7, 0, -2, -3, -4.5, 10, 1, 1, 1, 0, 9, 5]
    
    def getTime(self, str_date, rssitem):

        #GMT+00:00
        try:
            offset = 0
            found = False
            try:
                match = re.search('[-+][0-9]{4}', str_date)
                result = match.group(0)
                h = result[1:3]
                m = result[3:5]
                offset = int(h) * 3600 + int(m) * 60
                
                if result[0] == '-':
                    offset *= -1
                    
                str_date = str_date.replace(result, "GMT")
                found = True
            except:
                try:
                    match = re.search('GMT[-+][0-9]{2}:[0-9]{2}', str_date)
                    result = match.group(0)
                    
                    h = result[4:6]
                    m = result[7:9]
                    offset = int(h) * 3600 + int(m) * 60
                    
                    if result[0] == '-':
                        offset *= -1
                    
                    str_date = str_date.replace(result, "GMT")
                    found = True
                except:
                    pass
            
            if found == False:
                for i in range(0, len(self.zones)):
                    if self.zones[i] in str_date:
                        offset = self.zonesoffset[i] * 3600
                        str_date = str_date.replace(self.zones[i], "GMT")
                        break
            
            
            czas = time.mktime( time.strptime(str_date, "%a, %d %b %Y %H:%M:%S %Z"))
            czas += offset
            
            rssitem.date_int = czas
            rssitem.date = time.strftime('%a, %d %b %Y %H:%M:%S', time.gmtime(czas))
        except:
            rssitem.date_int = 0
            rssitem.date = 'N\A lol %s' % str_date
            
class RSSParser:
    def __init__(self):
        self.dom = None
        self.source = None
    
    def parseXML_new(self):
        del self.source.channels[:]
        channels = self.dom.getElementsByTagName('channel')
        for channelXML in channels:
            channel = RSSChannel()
            self.source.channels.append(channel)
            for channelNode in channelXML.childNodes:
                print channelNode.data
          
            
        pass
    
    
    
    def parseXML(self):
        #parse - get channel
        del self.source.channels[:]
        channels = self.dom.getElementsByTagName('channel')
        for channelXML in channels:
            channel = RSSChannel()
            channel.title = channelXML.getElementsByTagName('title')[0].childNodes[0].data
            #print 'CHAN: %s' % channel.title
            descs = channelXML.getElementsByTagName('description')
            if len(descs) > 0 and len(descs[0].childNodes) > 0:
                channel.description = descs[0].childNodes[0].data
                
            channel.link = channelXML.getElementsByTagName('link')[0].childNodes[0].data
            #print ' CHANNEL: %s' % channel.link
            self.source.channels.append(channel)
            items = channelXML.getElementsByTagName('item')
            if len(items) == 0:
                items = channelXML.getElementsByTagName('entry')
            
            channel.read = True

            for itemXML in items:
                item = RSSItem()
                item.title = itemXML.getElementsByTagName('title')[0].childNodes[0].data
                item.link = itemXML.getElementsByTagName('link')[0].childNodes[0].data
                descs = itemXML.getElementsByTagName('content:encoded')
                
                if len(descs) == 0:
                    descs = itemXML.getElementsByTagName('description')
                if len(descs) == 0:
                    descs = itemXML.getElementsByTagName('content')
               
                if len(descs) != 0:
                    item.description = descs[0].childNodes[0].data
                
                dates = itemXML.getElementsByTagName('pubDate')
                if len(dates) == 0:
                    dates = itemXML.getElementsByTagName('updated')
                
                if len(dates) != 0:
                    str_date = dates[0].childNodes[0].data
                    tzh.getTime(str_date, item)
                
                enclosures = itemXML.getElementsByTagName('enclosure')
                for enc in enclosures:
                    try:
                        type = enc.attributes['type'].nodeValue
                        
                        if len(type) > 1 and 'image/' in type:
                            url = enc.attributes['url'].nodeValue
                            item.imageURLS.append(url)
                        if len(type) > 1 and 'video/' in type:
                            url = enc.getAttribute('url')
                            item.video = url
                    except:
                        pass
                
                if self.includeHTMLsIMG:
                    self.ReadIMG(item, item.description)
                    
                groups = itemXML.getElementsByTagName('media:group')
                if len(groups) > 0:
                    medias = groups[0].getElementsByTagName('media:content')
                else:
                    
                    medias = itemXML.getElementsByTagName('media:content')
                
                for media in medias:
                    try:
                        type = media.attributes['medium'].nodeValue
                        if 'image' in type:
                            curl = media.getAttribute('url')
                            item.imageURLS.append(curl)
                            break
                    except:
                        try:
                            curl= media.attributes['url'].nodeValue
                            if (not self.ReadMedia(item, curl)):
                                type = media.attributes['type'].nodeValue
                                if len(type) > 1 and 'image/' in type:
                                    url = media.getAttribute('url')
                                    item.imageURLS.append(url)
                                if len(type) > 1 and 'video/' in type:
                                    url = media.getAttribute('url')
                                    item.video = url
                        except:
                            pass
                
                try:
                    if len(item.imageURLS) == 0:
                        thumbs = itemXML.getElementsByTagName('media:thumbnail')
                        for thumb in thumbs:
                            item.imageURLS.append(thumb.attributes['url'].nodeValue)
                except:
                    pass
                
                records = re.findall( '<embed(.+?)src="(.+?)"(.*?)>(.*?)</embed>', item.description, re.DOTALL )
                for record in records:
                    self.ReadYT(item, record[1]);

                #<br> -> \n
                nap = item.description
                item.description = re.sub('(<[bB][rR][ /]>)|(<[/ ]*[pP]>)', '[CR]', item.description, re.DOTALL)
                    
                item.channel = channel
                channel.items.append(item)
                
                if self.imageCachingEnabled and len(item.imageURLS) > 0:
                    self.PrepareCacheDirs(item)
                    imageCacher.enqueue(item)
                    for imageU in item.imageURLS:
                        im = getCacheThumbName(imageU, item.multiimagepath)
                        if not im in item.image:
                            item.image.append(im)
                elif not self.imageCachingEnabled:
                    for imageU in item.imageURLS:
                        item.image.append(imageU)
        
    def ReadMedia(self, item, string):
        retval = self.ReadYT(item, string);
        if retval == False:
            retval = self.ReadIMG(item, string);
            
        return retval

    def PrepareCacheDirs(self, item):
        chandirname = xbmc.getCacheThumbName(item.channel.link).replace(".tbn","")
        tpath = xbmc.translatePath('special://masterprofile/Thumbnails/RSS/%s' % chandirname)
        checkDir(tpath)

        itemdirname = xbmc.getCacheThumbName(item.link).replace(".tbn","")
        tpath = os.path.join(tpath, itemdirname)
        checkDir(tpath)

        item.multiimagepath = tpath
        
    def ReadYT(self, item, string):
        if 'youtube.com/v' in string:
            vid_ids = re.findall('http://www.youtube.com/v/(.{11})\??', string, re.DOTALL )
            for id in vid_ids:
                item.video = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % id
                return True

        return False
    
    def ReadIMG(self, item, string):
        found = False
        if 'img' in string and 'src' in string:
            img_srcs = re.findall('(<|&lt;).*?src=("|&quot;)(.*?)("|&quot;)', string, re.DOTALL)
            for src in img_srcs:
                item.imageURLS.append(src[2]);
                found = True
                #print 'image %s' % item.image

        return found;
    
    
    def readFromCache(self, src):
        self.source = src
        file = self.source.url.replace("http://","").replace("/", "_").replace("\\", "_").replace("?", "_").replace(";","_").replace("&","amp;")
        path = os.path.join(DATA_PATH, '%s.txt' % file)
        
        if not os.path.exists(path):
            return False
        
        log('Reading from cache (%s)' % self.source.url)
        
        f = open(path, 'r')
        xmlDocument = f.read()
        f.close()
        
        self.dom = xml.dom.minidom.parseString( str(xmlDocument))
        self.parseXML()
        
        dltimes = self.dom.getElementsByTagName('dltime')
        if len(dltimes) > 0:
            self.source.lastupdate = float(dltimes[0].childNodes[0].data)
        
        
    def readFromURL(self, src):
        self.source = src
        log('Reading from internet (%s)' % self.source.url)

        encurl = self.source.url.replace("amp;", "&").replace(' ', '%20')
        #print 'MYURL = %s' % encurl
        
        f = urllib.urlopen(  encurl  )
        
        xmlDocument = f.read()
        f.close()
        self.dom = xml.dom.minidom.parseString( str(xmlDocument))

        self.parseXML()
        
        self.source.lastupdate = time.time()
        
        file = self.source.url.replace("http://","").replace("/", "_").replace("\\", "_").replace("?", "_").replace(";","_").replace("&","amp;")
        path = os.path.join(DATA_PATH, '%s.txt' % file)
        
        document = self.dom.documentElement
        
        dl = self.dom.createElement('dltime')
        dl.appendChild(self.dom.createTextNode(str(src.lastupdate)))
        document.appendChild(dl)
        
        newxml = document.toxml('utf_8')    
        file = open(path, 'w')
        file.write(newxml)
        file.close()
        
        
    
    def checkCache(self):
        return False
    
    
class RSSReader:
    def __init__(self):
        pass
    
    def setImageCaching(self, im):
        self.imageCachingEnabled = im
        
    def setIncludeHTMLimg(self, img):
        self.includeHTMLsIMG = img
    
    def StopCachingImages(self):
        imageCacher.alarmExit();
    
    def ReadSets(self, sets, fromcache):
        #bgReadSet = BackgroundRSSReaderReadSets(sets, self)
        #bgReadSet.setDaemon(True)
        #bgReadSet.start()
        
        for set in sets:
            self.ReadSet(set, fromcache)
        
            
    def ReadSet(self, set, fromcache):
        self.ReadSources(set.sources, fromcache)
            
    def ReadSources(self, srcs, fromcache):
        for src in srcs:
            self.ReadSource(src, fromcache)
            
    def ReadSourceBoth(self, src):
        try:
            self.ReadSource(src, True)
        except:
            self.ReadSource(src, False)
            
    def ReadSource(self, src, fromcache):
        try:
            parser = RSSParser()
            parser.includeHTMLsIMG = self.includeHTMLsIMG
            parser.imageCachingEnabled = self.imageCachingEnabled
            
            if fromcache:
                parser.readFromCache(src)
            else:
                parser.readFromURL(src)

        except :
            pass


class RSSFeedsListLoader:
    def __init__(self):
        self.listXML = None
        self.setList = []
        self.loadFile()
        self.parseFile()
        
    def loadFile(self):
        path = os.path.join(CWD, "../../userdata/RssFeeds.xml")
        try:
            f = open(path)
        except IOError:
            return
        
        fl = f.read()
        f.close()
        fl = fl.replace('&', 'amp;')
        #fl = fl.replace('=', 'apos;')
        #fl = fl.replace('apos;\"', '=\"')
        
        self.listXML = xml.dom.minidom.parseString(fl)
        
    
    def parseFile(self):
        sets = self.listXML.getElementsByTagName('set')
        del self.setList[:]
        for setXML in sets:
            set = RSSSet()
            set.id = setXML.attributes['id'].nodeValue
            feeds = setXML.getElementsByTagName('feed')
            for feedXML in feeds:
                src = RSSSource()
                src.url = feedXML.childNodes[0].nodeValue
                src.updateinterval = feedXML.attributes['updateinterval'].nodeValue
                set.sources.append(src)
            self.setList.append(set)
            
    def getRSSSets(self):
        return self.setList
    
tzh = TimeZoneHandler()
imageCacher = ImageCacher()