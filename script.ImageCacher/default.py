import xbmc, os, urllib, xbmcgui

XBMC_DELAY = 100
DEBUG_ENABLED = True

def log(txt):
    if DEBUG_ENABLED:
        print 'LOG script.ImageCacher: %s' % txt

def checkDir(path):
    if not os.path.exists(path):
        os.mkdir(path)
        
def getCacheThumbName(url, CachePath):
    thumb = xbmc.getCacheThumbName(url)
           
    if 'jpg' in url:
        thumb = thumb.replace('.tbn', '.jpg')
    elif 'png' in url:
        thumb = thumb.replace('.tbn', '.png')
    elif 'gif' in url:
        thumb = thumb.replace('.tbn', '.gif')           
    
    tpath = os.path.join(CachePath, thumb)
    return tpath

def download(src,dst):
    #first cache
    tmpname = xbmc.translatePath('special://temp/%s' % xbmc.getCacheThumbName(src))
    
    if os.path.exists(tmpname):
        os.remove(tmpname)
    
    urllib.urlretrieve(src, filename = tmpname)
    os.rename(tmpname, dst)
    
PropertyName = 'CachedImagesPath'
CacheName = None
ImagesStr = ''
Separator = ';'
OnlyIfMoreThanOne = True
Window = None
#Run only if more than 2
#RunScript(script.ImageCacher,window=propertyname=ImagePath,separator=;,cachename=optional,images=im)

log(str(sys.argv))

for arg in sys.argv:
    param = arg.lower()
    
    if param == 'script.imagecacher':
        continue
    
    elif param.startswith('propertyname='):
        PropertyName = arg[13:]
    
    elif param.startswith('cachename='):
        CacheName = arg[10:]
        
    elif param.startswith('images='):
        ImagesStr = arg[7:]
        
    elif param.startswith('separator='):
        Separator = arg[10:]

    elif param == 'window':
        Window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    elif param.startswith('window='):
        Window = xbmcgui.Window(int(arg[7:]))
    elif param == 'dialog':
        Window = xbmcgui.WindowDialog(xbmcgui.getCurrentWindowDialogId())
    elif param.startswith('dialog='):
        test = int(arg[7:])
        Window = xbmcgui.WindowDialog(int(arg[7:])) 
                
    elif param.startswith('force='):
        if param[6:] == 'true':
            OnlyIfMoreThanOne = False
    
    elif param.startswith('debug='):
        if param[6:] == 'true':
            DEBUG_ENABLED = True
        

if Window == None:
    Window = xbmcgui.Window(xbmcgui.getCurrentWindowId())

Window.setProperty(PropertyName, '')

log('Set to null property name')

Images = ImagesStr.split(Separator)
log(str(Images))

for Im in Images:
    if len(Im) == 0:
        Images.remove(Im)

if (len(Images) < 2 and OnlyIfMoreThanOne) or len(Images) == 0:
    sys.exit()

if CacheName == None: #if not specified - create are own name of directory
    CacheName = xbmc.getCacheThumbName(ImagesStr).replace('.tbn', '')

checkDir(xbmc.translatePath('special://masterprofile/Thumbnails/ImageCacher'))

CacheDir = xbmc.translatePath('special://masterprofile/Thumbnails/ImageCacher/%s' % CacheName)
checkDir(CacheDir)

log('CacheDir = %s' % CacheDir)

files = os.listdir(CacheDir)

#Check if there are images already:
ThereIsImageAlready = False
for file in files:
    if (file.endswith('jpg') or file.endswith('png') or file.endswith('tbn') ) and os.path.getsize(os.path.join(CacheDir, file)) > 999:
        log('We have cached files already - updating path property')
        Window.setProperty(PropertyName, CacheDir)
        ThereIsImageAlready = True
        break

NewFiles = 0

for img in Images:
    if xbmc.abortRequested:
        sys.exit()
    
    path = getCacheThumbName(img, CacheDir)
    if not os.path.exists(path):
        download(img, path)
        if os.path.getsize(path) > 999: #it's actual image and not some blank stuff
            log('Cached %s to %s' % (img, path) )
            
            if not ThereIsImageAlready:
                log('We cached first image - updating path property')
                Window.setProperty(PropertyName, '')
                xbmc.sleep(XBMC_DELAY)
                Window.setProperty(PropertyName, CacheDir)
                ThereIsImageAlready = True
            else:
                NewFiles = NewFiles + 1
        
if NewFiles > 0:
    log('We finished caching files - updating path property')
    Window.setProperty(PropertyName, '')
    xbmc.sleep(XBMC_DELAY)
    Window.setProperty(PropertyName, CacheDir)   