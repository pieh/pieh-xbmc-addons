'''
Created on 2010-12-16

@author: Misiek
'''
import sys
import xbmcgui
from xbmcgui import Window

RSSid = -1
prefix = ''

for arg in sys.argv:
    param = arg.lower()
    if 'prefix=' in param:
        prefix = param.replace('prefix=', '')
        if not prefix.endswith('.'):
            prefix = prefix + '.'
    elif 'id=' in param:
        RSSid = param.replace('id=', '') 
        

if RSSid > -1:
    okno = Window(xbmcgui.getCurrentWindowId())
    
    okno.setProperty('RSS.Title', okno.getProperty('%sRSS.%s.Title' % (prefix, RSSid)  ))
    okno.setProperty('RSS.Desc', okno.getProperty('%sRSS.%s.Desc' % (prefix, RSSid)  ))
    okno.setProperty('RSS.Image', okno.getProperty('%sRSS.%s.Image' % (prefix, RSSid)  ))
    
    okno.setProperty('RSS.Date', okno.getProperty('%sRSS.%s.Date' % (prefix, RSSid)  ))
    okno.setProperty('RSS.Channel', okno.getProperty('%sRSS.%s.Channel' % (prefix, RSSid)))
    okno.setProperty('RSS.Media', okno.getProperty('%sRSS.%s.Media' % (prefix, RSSid)))
    okno.setProperty('RSS.MultiImagePath', okno.getProperty('%sRSS.%s.MultiImagePath' % (prefix, RSSid)))
    okno.setProperty('RSS.SlideShowable', okno.getProperty('%sRSS.%s.SlideShowable' % (prefix, RSSid)))
    okno.setProperty('RSS.ID',  RSSid)
    
    i_count = okno.getProperty('%sRSS.%s.ImageCount' % (prefix, RSSid))
    
    okno.setProperty('RSS.ImageCount', i_count)
    for i in range(1, int(i_count)+1):
        okno.setProperty('RSS.Image.%d' % i, okno.getProperty('%sRSS.%s.Image.%d' % (prefix, RSSid, i)))
        