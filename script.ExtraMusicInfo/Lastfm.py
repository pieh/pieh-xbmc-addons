import xml.dom.minidom
from Utils import log, GetStringFromUrl, GetValue

lastfm_apikey = 'b25b959554ed76058ac220b7b2e0a026'

def GetSimiliarById(m_id):
    url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&mbid=%s&api_key=%s' % (m_id, lastfm_apikey)
    ret = GetStringFromUrl(url)
    
    curXML = xml.dom.minidom.parseString(ret)
    
    curXMLs = curXML.getElementsByTagName('lfm')
    if len(curXMLs) > 0:
        curXML = curXMLs[0]
    else:
        return
    
    curXMLs = curXML.getElementsByTagName('similarartists')
    if len(curXMLs) > 0:
        curXML = curXMLs[0]
    else:
        return
        
    artistXMLs = curXML.getElementsByTagName('artist')
    
    similiars = []
    
    for artistXML in artistXMLs:
        artist = {"name": GetValue(artistXML, 'name'), "mbid": GetValue(artistXML, 'mbid')}
        similiars.append(artist)
    
    log('Found %i Similiar artists in last.FM' % len(similiars))
    
    return similiars