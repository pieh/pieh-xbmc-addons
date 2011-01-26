import urllib, os.path, xbmc, re, htmlentitydefs, time

from xbmcgui import Window
from threading import Thread
from threading import Lock
import xbmcaddon
import xbmcgui, sys
#import rss
from rss import ImageCacher, RSSFeedsListLoader, RSSReader, RSSSet, RSSSource, TimeZoneHandler

REMOTE_DBG = False 

# append pydev remote debugger
if REMOTE_DBG:
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)

ACTION_EXIT_SCRIPT = ( 9, 10, 110)
ACTION_INFO = [11]
ACTION_SELECT = (7, 12,)
ACTION_PLAY = [79]

DATA_PATH = xbmc.translatePath( "special://profile/addon_data/script.rssclient/")
if not os.path.exists(DATA_PATH): os.makedirs(DATA_PATH)

args = ''
feeds = [ ]
limit = 20
controlListId = -1

addon = xbmcaddon.Addon('script.rssclient-standalone')

includeHTMLsIMG = addon.getSetting('htmlimg') in ['true', 'True', 1]
imageCachingEnabled = addon.getSetting('imagecaching') in ['true', 'True', 1]
ui = None
# Current Working Directory
CWD = os.getcwd()
if CWD[-1] == ';': CWD = CWD[0:-1]
if CWD[-1] != '\\': CWD = CWD + '\\'

already_read = []

textureDBpath = ''

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

def checkDir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        
def download(src,dst):
    tmpname = xbmc.translatePath('special://temp/%s' % xbmc.getCacheThumbName(src))
    
    if os.path.exists(tmpname):
        os.remove(tmpname)
    
    urllib.urlretrieve(src, filename = tmpname)
    os.rename(tmpname, dst)
    
def UnreadTopCompare(x, y):
    xa = x.getProperty('read')
    ya = y.getProperty('read')
    
    if len(xa) < 2: xa = 'false'
    if len(ya) < 2: ya = 'false'
    
    if xa == 'true' and ya == 'false':
        return 1
    elif xa =='false' and ya =='true':
        return -1
    else:
        return 0
    
def DateCompare(x, y):
    if ui != None and ui.unreadontop:
        val = UnreadTopCompare(x, y)
        if val != 0: return val
        
    if ui != None and ui.groupbychannel:
        val = ChannelCompare(x, y)
        if val != 0: return val
    
    xa = ya = 0
    
    if 'ListItem' in str(type(x)):
        xa = float(x.getProperty('dateint'))
        ya = float(y.getProperty('dateint'))
    else:
        xa = float(x.date_int)
        ya = float(y.date_int)
    
    if xa < ya:
        return 1
    elif xa > ya:
        return -1
    else:
        return 0
    
def ChannelCompare(x, y):
    if ui.unreadontop:
        val = UnreadTopCompare(x, y)
        if val != 0: return val
        
    xa = x.getProperty('channeltext')
    ya = y.getProperty('channeltext')
    
    if xa < ya:
        return -1
    elif xa > ya:
        return 1
    else:
        return 0
    
def TitleCompare(x, y):
    if ui.groupbychannel:
        val = ChannelCompare(x, y)
        if val != 0: return val
    
    if ui.unreadontop:
        val = UnreadTopCompare(x, y)
        if val != 0: return val
        
    xa = x.getLabel()
    ya = y.getLabel()
    
    if xa < ya:
        return -1
    elif xa > ya:
        return 1
    else:
        return 0
    
def log(txt):
    print 'LOG script.rssclient: %s' % txt

def htmlentitydecode(s):
    # code from http://snipplr.com/view.php?codeview&id=15261
    # First convert alpha entities (such as &eacute;)
    # (Inspired from http://mail.python.org/pipermail/python-list/2007-June/443813.html)
    def entity2char(m):
        entity = m.group(1)
        if entity in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[entity])
        return u" "  # Unknown entity: We replace with a space.
    
    t = re.sub(u'&(%s);' % u'|'.join(htmlentitydefs.name2codepoint), entity2char, s)
  
    # Then convert numerical entities (such as &#233;)
    t = re.sub(u'&#(\d+);', lambda x: unichr(int(x.group(1))), t)
   
    # Then convert hexa entities (such as &#x00E9;)
    return re.sub(u'&#x(\w+);', lambda x: unichr(int(x.group(1),16)), t)

def cleanText(txt):
    p = re.compile(r'\s+')
    txt = p.sub(' ', txt)
    
    txt = htmlentitydecode(txt)
    
    p = re.compile(r'<[^<]*?/?>')
    return p.sub('', txt)

def addItemToList(item, myList):
    liz = xbmcgui.ListItem(item.title)
    liz.setProperty('desc', cleanText(item.description))
    liz.setProperty('link', item.link)
    if len(item.image) > 0:
        liz.setProperty('image', item.image[0])
    else:
        #print 'EMPTY ITEM = %s -> %s' % (item.channel.link, item.link)
        liz.setProperty('image', '')
    
    i = 1
    for image in item.image:
        liz.setProperty('image.%d' % i, image)
        i = i + 1
    
    liz.setProperty('imageCount', str(len(item.image)))
    
    val= (((imageCachingEnabled and len(item.image) > 1) and ['true'] or ['false'])[0])
    liz.setProperty('slideshowable', val)

    
    liz.setProperty('multiimagepath', item.multiimagepath)
    
    liz.setProperty('date', item.date)
    liz.setProperty('dateint',str(item.date_int))
    liz.setProperty('video', item.video)
    
    if item.channel != None:
        liz.setProperty('channeltext', item.channel.title)
        liz.setProperty('channellink', item.channel.link)

    #self.itemList.addItem(liz)
    if item.read:
        liz.setProperty('read', ((item.read and ['true'] or ['false'])[0]))
        
    item.liz = liz
    
    myList.append(liz)
    return liz;



class VideoGUI(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs ):
        xbmcgui.WindowXML.__init__( self, *args, **kwargs )
        self.sets = []
        self.readstatusassigner = BGStatusAssigner()
        self.sortmodes = ['Title', 'Date']
        self.sortmode = 1
        self.items = []
        self.sortdesc = False
        self.hideread = False
        self.unreadontop = False
        self.groupbychannel = False
        self.currentChan = '#all'
        self.currentItem = ''
        self.isReady = False
        self.selectBuiltin = None
        
        
    def onInit(self):
        self.channelList =  self.getControl(30051)
        self.itemList = self.getControl(30050)
        
        self.image = self.getControl(30011)
        self.justtext = self.getControl(30009)
        #self.textandimage = self.getControl(30010)
        #self.dateLabel = self.getControl(30008)
        self.sortButton =self.getControl(39003)
        
        self.isReady = True
        self.channelList.selectItem(0)
        self.updateChannelList()
        self.lastlistmovement = time.time()
        self.updateSortButton()


    def updateSortButton(self):
        self.sortButton.setLabel("SORT BY: %s" % self.sortmodes[self.sortmode])
        self.updateItemListWork(True)
        
    def updateChannelList(self):
        if not self.updateChannelListWork(False):
            self.updateChannelListWork(True)
        
    def updateChannelListWork(self, force_reset):
        lock = Lock()
        lock.acquire()


        actualitems = []

        if force_reset:
            log('Channel list update')        
            self.channelList.reset()

            liz = xbmcgui.ListItem(addon.getLocalizedString(30005))
            liz.setProperty('link', '#all')
            self.channelList.addItem(liz)
        else:
            try:
                i = 0
                while True:
                    actualitems.append(self.channelList.getListItem(i))
                    i += 1
            except:
                pass
            
        
        pos = 0
        i = 1
        for set in self.sets:
            #print 'LOG set %s' % set.id
            for source in set.sources:
                #print 'LOG src %s' % source.url
                for channel in source.channels:
                    if force_reset:
                        liz = xbmcgui.ListItem(channel.title)
                        
                        liz.setProperty('link', channel.link)
                        #liz.setProperty('link', channel.link)
                        self.channelList.addItem(liz)
                        
                        if channel.link == self.currentChan:
                            pos = i
                        
                        i += 1
                    else:
                        wasntbefore = True
                        for item in actualitems:
                            if item.getProperty('link') == channel.link:
                                wasntbefore = False
                                break
                        
                        if wasntbefore:
                            return False
                            
        
        if force_reset:
            self.channelList.selectItem(pos)
            
        self.checkIfChannelRead('#all')
        self.updateItemList()
        
        lock.release()
        return True
            
            
    def updateItemList(self):
        if not self.updateItemListWork(False):
            self.updateItemListWork(True)
            self.checkIfChannelRead('#all')
            
    def updateItemListWork(self, force_reset):
        lock = Lock()
        lock.acquire()
        
        
        actualitems = []
        if force_reset:
            self.clearItems()
        else:
            try:
                i = 0
                while True:
                    actualitems.append(self.itemList.getListItem(i))
                    i += 1
            except:
                pass
        
        i = 0
        
        if self.currentChan == '#all':
            #print 'current channel'
            for set in self.sets:
                for source in set.sources:
                    for channel in source.channels:
                        for item in channel.items:
                            #print 'ITEM %s' % item.link
                            if force_reset:
                                self.addItem(item)
                            else:
                                wasntbefore = True

                                for item_before in actualitems:
                                    if item_before.getProperty('link') == item.link:
                                        wasntbefore = False
                                        actualitems.remove(item_before)
                                        i -= 1
                                        break
                                
                                if wasntbefore:
                                    lock.release()
                                    return False
                            
                            i += 1
            if force_reset:
                self.putItems()
                self.updateText()
            else:
                if len(actualitems) > 0 or i > 0:
                    lock.release()
                    return False
            
            lock.release()
            return True

        else:
            #print 'other channel'
            for set in self.sets:
                for source in set.sources:
                    for channel in source.channels:
                        if channel.link == self.currentChan:
                            for item in channel.items:
                                #print 'ITEM %s' % item.link
                                if force_reset:
                                    self.addItem(item)
                                else:
                                    wasntbefore = True
                                    for item_before in actualitems:
                                        if item_before.getProperty('link') == item.link:
                                            wasntbefore = False
                                            actualitems.remove(item_before)
                                            i -= 1
                                            break
                                    
                                    if wasntbefore:
                                        lock.release()
                                        return False
                                    
                                i += 1
                            
                            if force_reset:    
                                self.putItems()
                                self.updateText()
                            else:
                                if len(actualitems) > 0 or i > 0:
                                    lock.release()
                                    return False
                                
                            lock.release()

                            return True
                        
    def clearItems(self):
        del self.items[:]
    
    def putItems(self):
        #sorting etc
        #self.sortmodes = ['Title', 'Channel', 'Date']
        items = []
        
        if self.sortmode == 0: 
            items = sorted(self.items, cmp=TitleCompare, reverse = self.sortdesc )
        elif self.sortmode == 1:
            items = sorted(self.items, cmp=DateCompare, reverse = self.sortdesc )
        
        
        firstlink = 'N/A'
        i = 0
        pos = -1
        self.itemList.reset()
        for item in items:
            if i == 0: firstlink = item.getProperty('link')
            
            if item.getProperty('link') == self.currentItem:
                pos = i
            self.itemList.addItem(item)
            i+=1
        
        if pos >= 0:
            self.itemList.selectItem(pos)
        else:
            self.itemList.selectItem(pos)
            self.currentItem = firstlink

        self.readstatusassigner.set(self.currentItem)
        self.readstatusassigner.start()
        self.clearItems()
        
    
    def addItem(self, item):
        addItemToList(item, self.items)
           
        #self.setJustItemAsRead(item.link, item.read, False)
                        
    def onControl(self, control):
        pass
    
    def onFocus(self, controlID):
        pass
    
    def getLizFromItems(self, link):
        try:
            i = 0
            while True:
                liz = self.itemList.getListItem(i)
                if liz.getProperty('link') == link:
                    return liz
                i += 1
        except:
            pass
        
        return None
    
    def getLizFromChannels(self, link):
        try:
            i = 0
            while True:
                liz = self.channelList.getListItem(i)
                if liz.getProperty('link') == link:
                    return liz
                i += 1
        except:
            pass
        
        return None 

    def getChannelFromSets(self, link):
        for set in self.sets:
            for source in set.sources:
                for channel in source.channels:
                    if channel.link == link:
                        return channel
                    
        
    def getItemFromSets(self, link):
        for set in self.sets:
            for source in set.sources:
                for channel in source.channels:
                    for item in channel.items:
                        if item.link == link:
                            return item
                            
    def onAction(self, action):
        if ( action in ACTION_EXIT_SCRIPT ):
            readstatusarchiver = RSSReadStatusArchiver()
            readstatusarchiver.Save(self.sets)
            reader.StopCachingImages()
            self.close()
        else:
            id = self.getFocusId()
            if id == 30051:
                if action in ACTION_SELECT:
                    #TODO marking channel as read
                    #item = self.getChannelFromSets(self.currentChan)
                    pass
                else:
                    liz = self.channelList.getSelectedItem()
                    channelProp = liz.getProperty('link')
                    if self.currentChan != channelProp:
                        self.currentChan = channelProp
                        self.updateItemList()
                    
            elif id == 30050:
                if action in ACTION_SELECT:
                    if self.selectBuiltin == None:
                        self.selectBuiltin = self.getProperty('onItemSelect')

                    if self.selectBuiltin == '':
                        self.setItemAsRead(self.currentItem, True, True)
                    else:
                        xbmc.executebuiltin(self.selectBuiltin)
                elif action in ACTION_PLAY:
                    liz = self.itemList.getSelectedItem()
                    video = liz.getProperty('video')
                    
                    if( len(video) > 0):
                        if ',' in video:
                           xbmc.Player().play(video)
                        else:
                            xbmc.executebuiltin("XBMC.PlayMedia(%s)" % ( video) )
                elif action in ACTION_INFO:
                    if imageCachingEnabled:
                        liz = self.itemList.getSelectedItem()
                        try:
                            c = int(liz.getProperty('imageCount'))
                            
                            log('OBRAZKOW = %d' % c)
                            for i in range(1, c+1):
                                arg = 'image.%d' % (i)
                                napis = liz.getProperty(arg)
                                log('    %s = %s' % (arg, napis))
                            
                            if c > 1:
                                multiimagepath = liz.getProperty('multiimagepath')
                                xbmc.executebuiltin("XBMC.SlideShow(%s)" % multiimagepath)
                            else:
                                log('za malo obrazkow')
                                pass
                        except:
                            pass
                else:
                    liz = self.itemList.getSelectedItem()
                    itemProp = liz.getProperty('link')
                    
                    if self.currentItem != itemProp:
                        self.currentItem = itemProp
                        self.updateText()
                        
                        self.readstatusassigner.set(itemProp)
                        self.readstatusassigner.start()
                        
            elif id == 39003 and action in ACTION_SELECT:
                self.sortmode = (self.sortmode + 1) % len(self.sortmodes)
                self.updateSortButton()
            elif id == 39004 and action in ACTION_SELECT:
                self.sortdesc = not self.sortdesc
                self.updateSortButton()
            elif id == 39007 and action in ACTION_SELECT:
                self.groupbychannel = not self.groupbychannel
                self.updateSortButton()
            elif id == 39009 and action in ACTION_SELECT:
                self.setAsRead(self.currentChan)
            elif id == 39999 and action in ACTION_SELECT:
                addon.openSettings()
                print 'lol'

                tmp_includeHTMLsIMG = addon.getSetting('htmlimg') in ['true', 'True', 1]
                tmp_imageCachingEnabled = addon.getSetting('imagecaching') in ['true', 'True', 1]
                
                reader.setImageCaching(tmp_includeHTMLsIMG)
                reader.setIncludeHTMLimg(tmp_imageCachingEnabled)
                bgReadSet = BackgroundRSSReaderReadSets(sets, reader)
                bgReadSet.setDaemon(True)
                bgReadSet.start()
            else:
                return
            
    def setAsRead(self, channellink):
        for set in self.sets:
            for source in set.sources:
                for channel in source.channels:
                    if channellink == '#all' or channellink == channel.link:
                        for item in channel.items:
                            self.setJustItemAsRead(item.link, True, False)
        
        self.checkIfChannelRead(channellink)
                        
    def checkIfChannelRead(self, channellink):
        allread = True
        for set in self.sets:
            for source in set.sources:
                for channel in source.channels:
                    if channellink == '#all' or channellink == channel.link:
                        chanread = True
                        
                        for item in channel.items:
                            if not item.read:
                                chanread = allread = False
                                
                        channel.read = chanread
                        liz = self.getLizFromChannels(channel.link)
                        if liz != None:
                            liz.setProperty('read', ((chanread and ['true'] or ['false'])[0]))
                                
        if allread == False:
            liz = self.getLizFromChannels('#all')
            if liz != None:
                liz.setProperty('read', ((allread and ['true'] or ['false'])[0]))
        

    def setJustItemAsRead(self, link, read, inverse):
        item = self.getItemFromSets(link)
        if inverse: 
            read = not item.read
        item.read = read
        liz = self.getLizFromItems(item.link)
        liz.setProperty('read', ((item.read and ['true'] or ['false'])[0]))
        
        if already_read.count(link) > 0:
            already_read.remove(link)
        else:
            already_read.append(link)
                             
    def setItemAsRead(self, link, read, inverse):
        self.setJustItemAsRead(link, read, inverse)
        liz = self.getLizFromItems(link)
        if liz == None: return
        chan = liz.getProperty('channellink')

        self.checkIfChannelRead(chan)
        
    def updateText(self):
        for set in self.sets:
            for source in set.sources:
                for channel in source.channels:
                    if channel.link == self.currentChan or self.currentChan == '#all':
                        for item in channel.items:
                            if item.link == self.currentItem:
                                #self.dateLabel.setLabel(item.date)
                                if len(item.image) > 0:
                                    #jest image

                                    self.image.setImage(item.image[0])
                                    if(type(self.justtext) == 'xbmcgui.ControlLabel' ):
                                        #self.textandimage.setLabel(self.cleanText(item.description))
                                        self.justtext.setLabel('')
                                    elif (type(self.justtext) == 'xbmcgui.ControlTextBox' ):
                                        #self.textandimage.setText(self.cleanText(item.description))
                                        self.justtext.setText('')
                                else:
                                    self.image.setImage('')
                                    if(type(self.justtext) == 'xbmcgui.ControlLabel' ):
                                        self.justtext.setLabel(self.cleanText(item.description))
                                        #self.textandimage.setLabel('') 
                                    elif (type(self.justtext) == 'xbmcgui.ControlTextBox' ):
                                        self.justtext.setText(self.cleanText(item.description))
                                        #self.textandimage.setText('')
    
    def onClick(self, controlID):
        #print 'CID %d' % controlID
        return
        
class BGStatusAssigner(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.reset()
        self.id = 0
    
    def set(self, link):
        self.link = link
        self.id += 1
      
    def reset(self):
        self.link = ''
        
    def run(self):
        try:
            link = self.link
            id = self.id
            
            time.sleep(1.5)
            
            if link == self.link and self.id == id:
                ui.setItemAsRead(link, True, False)
                
        except:
            pass


class RSSReadStatusArchiver:
    def __init__(self):
        pass
    
    def Save(self, sets):
        for set in sets:
            for source in set.sources:
                file = source.url.replace("http://","").replace("/", "_").replace("\\", "_").replace("?", "_").replace(";","_").replace("&","_")
                path = os.path.join(DATA_PATH, '%s_readstatus.txt' % file)
                
                file = open(path, 'w')
                
                for channel in source.channels:
                    for item in channel.items:
                        if item.read:
                            file.write('%s\n' % item.link)
                
                file.close()
        
    def Load(self, sets):
        
        del already_read[:]
        
        for set in sets:
            for source in set.sources:
                file = source.url.replace("http://","").replace("/", "_").replace("\\", "_").replace("?", "_").replace(";","_").replace("&","_")
                path = os.path.join(DATA_PATH, '%s_readstatus.txt' % file)
                
                if os.path.exists(path):
                    file = open(path, 'r')
                    links = file.read().split('\n')
                    file.close()
                    
                    already_read.extend(links)
                            


class BackgroundRSSReaderReadSets(Thread):
    
    def __init__(self, sets, reader):
        Thread.__init__(self)
        self.sets = sets
        self.setDaemon(True)
        self.reader = reader

    
    def run(self):
        okno = None
        try:
            okno = Window(xbmcgui.getCurrentWindowId())
            okno.setProperty('RSS.count', '0');
        except:
            pass
        unread_c = 0
        for set in self.sets:
            self.reader.ReadSet(set, True)
            for src in set.sources:
                for channel in src.channels:
                    unread_c += channel.unread_count
                    for item in channel.items:
                        if already_read.count(item.link) > 0:
                            item.read = True
                        else:
                            channel.unread_count += 1
                            channel.read = False

        log('All sets read from cache')  
          
        if ui != None and ui.isReady: ui.updateChannelList()
        
        changes = False
        
        next_update = -1
        
        for set in self.sets:
            for source in set.sources:
                last_checking = time.time() - source.lastupdate
                interval = int(source.updateinterval) * 60
                if last_checking > interval:
                    for src in set.sources:
                        for channel in src.channels:
                            unread_c -= channel.unread_count
                            
                    self.reader.ReadSource(source, False)
                    changes = True
                    for src in set.sources:
                        for channel in src.channels:
                            unread_c += channel.unread_count
                            for item in channel.items:
                                if already_read.count(item.link) > 0:
                                    item.read = True
                                else:
                                    channel.unread_count += 1
                                    channel.read = False
                    
                    if next_update == -1 or interval < next_update:
                        next_update = interval
                elif next_update == -1 or interval - last_checking < next_update:
                    next_update = interval - last_checking
        
        if changes:
            log('Sets updated from URL')    
            if ui != None and ui.isReady: ui.updateChannelList()


selectBuiltin = None

tmpSet = None
prefix = ''

for arg in sys.argv:

    param = str(arg).lower()
    if 'feed=' in param:
        feeds.append(param.replace('feed=', ''))

if ( __name__ == "__main__"):
    feedslist = RSSFeedsListLoader()
    sets = []
    selected_source = None

    if len(feeds) > 0 :
            tmpSet = RSSSet()
            tmpSet.id = 9999;
            
            for feed in feeds:
                source = RSSSource();
                source.url = feed;
                tmpSet.sources.append(source);
                
            sets.append(tmpSet);
    else:
        sets = feedslist.getRSSSets()
    
    readstatusarchiver = RSSReadStatusArchiver()
    readstatusarchiver.Load(sets)
    
    checkDir(xbmc.translatePath('special://masterprofile/Thumbnails/RSS'))
    
    ui = VideoGUI( "rss.xml", os.getcwd(), "default" )
    ui.selectBuiltin = selectBuiltin
    ui.sets = sets

    reader = RSSReader()
    reader.setImageCaching(imageCachingEnabled)
    reader.setIncludeHTMLimg(includeHTMLsIMG)
    #TODO !!!! 
    #reader.ReadSets(sets)
    bgReadSet = BackgroundRSSReaderReadSets(sets, reader)
    bgReadSet.setDaemon(True)
    bgReadSet.start()
    
    ui.updateChannelList()
    ui.doModal()
    del ui