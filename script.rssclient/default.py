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
createGui = True
feeds = [ ]
limit = 20
controlListId = -1
includeHTMLsIMG = True
imageCachingEnabled = True
ui = None
# Current Working Directory
CWD = os.getcwd()
if CWD[-1] == ';': CWD = CWD[0:-1]
if CWD[-1] != '\\': CWD = CWD + '\\'

already_read = []
addon = xbmcaddon.Addon('script.rssclient')
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

#items = sorted(self.items, cmp=DateCompare, reverse = self.sortdesc )
        try:
            okno.setProperty( "unread_rss", str(unread_c) )
            setting_script = xbmc.translatePath('special://home/addons/script.rssclient/set_properties.py')
            okno.setProperty('SettingScript', setting_script)
            itemList = []
            
            
            for set in self.sets:
                for source in set.sources:
                    for channel in source.channels:
                        for item in channel.items:
                            itemList.append(item)
            
            c = 1
            items = sorted(itemList, cmp=DateCompare, reverse = False )
            
            for item in items:
                if c <= limit:
                    okno.setProperty('%sRSS.%d.Title' % (prefix, c), item.title)
                    okno.setProperty('%sRSS.%d.Desc' % (prefix, c), cleanText(item.description))
                    
                    if len(item.image) > 0:
                        okno.setProperty('%sRSS.%d.Image' % (prefix, c), item.image[0])
                    else:
                        okno.setProperty('%sRSS.%d.Image' % (prefix, c), '')
                    
                    okno.setProperty('%sRSS.%d.ImageCount' % (prefix, c), str(len(item.image)) )
                    
                    
                    okno.setProperty('%sRSS.%d.SlideShowable' % (prefix, c), (( (imageCachingEnabled and len(item.image) > 1) and ['true'] or ['false'])[0]))
                    okno.setProperty('%sRSS.%d.MultiImagePath' % (prefix, c), item.multiimagepath)
                    
                    i = 1
                    for image in item.image:
                        okno.setProperty('%sRSS.%d.Image.%d' % (prefix, c,i), image)
                        i = i + 1
                    
                    if len(item.video) > 1:
                        okno.setProperty('%sRSS.%d.Media' % (prefix, c), item.video)
                    else:
                        okno.setProperty('%sRSS.%d.Media' % (prefix, c), '')
                    
                    
                    okno.setProperty('%sRSS.%d.Date' % (prefix, c), item.date.replace(',', '.'))
                    
                    if item.channel != None:
                        okno.setProperty('%sRSS.%d.Channel' % (prefix, c), item.channel.title)

                    c = c + 1;
                    
                    okno.setProperty('%sRSS.count' % prefix, str(c));
        except:
            pass

        if next_update > -1:
            alarmhash = xbmc.getCacheThumbName(args + str(time.localtime())).replace('.tbn', '')
            napis = 'AlarmClock(RSS_CHECK_%s,XBMC.RunScript(script.rssclient%s),%d,True)' % (alarmhash, args, ((next_update+60)  / 60.0))  
            log('Refresh in %d minutes' % ((next_update+60)  / 60.0))
            xbmc.executebuiltin(napis)

selectBuiltin = None
launchIt = True
tmpSet = None
prefix = ''

for arg in sys.argv:

    param = str(arg).lower()
    if 'onItemSelect=' in param:
        selectBuiltin = param.replace('onItemSelect=','')
    if param.startswith('prefix='):
        prefix = param.replace('prefix=', '')
        if not prefix.endswith('.'):
            prefix = prefix + '.'
    if 'feed=' in param:
        feeds.append(param.replace('feed=', ''))
    if 'limit=' in param:
        limit = int(param.replace('limit=', ''))
    if 'htmlimg=' in param:
        print 'htmlimg %s' % param
        if 'true' in param:
            includeHTMLsIMG = True
        elif 'false' in param:
            includeHTMLsIMG = False
            
    if 'imagecaching=' in param:
        if 'true' in param:
            imageCachingEnabled = True
        elif 'false' in param:
            imageCachingEnabled = False       
    if param != 'script.rssclient':
        args = args + ',' + arg    

if ( __name__ == "__main__" and launchIt):
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
    
    checkDir(xbmc.translatePath('special://masterprofile/Thumbnails/RSS'))
    
    reader = RSSReader()
    reader.setImageCaching(imageCachingEnabled)
    reader.setIncludeHTMLimg(includeHTMLsIMG)

    bgReadSet = BackgroundRSSReaderReadSets(sets, reader)
    bgReadSet.setDaemon(True)
    bgReadSet.start()
    