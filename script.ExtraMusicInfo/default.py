import xbmc,xbmcgui
import urllib
import xml.dom.minidom
import simplejson as json
import re
import time
import xbmcplugin
import os

from MusicBrainz import GetMusicBrainzId, SetMusicBrainzIDsForAllArtists
from BandsInTown import GetEvents
from Lastfm import GetSimiliarById
from Utils import log, GetStringFromUrl, GetValue, GetAttribute

def GetXBMCArtists():
    sqlQuery = "SELECT DISTINCT artist.strArtist, song.idArtist, song.strMusicBrainzArtistID FROM song JOIN artist ON artist.idArtist=song.idArtist"
    results = xbmc.executehttpapi( "QueryMusicDatabase(%s)" % urllib.quote_plus( sqlQuery ) )
    records = re.findall( "<record>(.+?)</record>", results, re.DOTALL )
    
    artists = []
    
    for record in records:
        fields = re.findall( "<field>(.+?)</field>", record, re.DOTALL)
        
        mbid = ''
        if len(fields) == 3:
            mbid = fields[2]
        
        artist = {"name": unicode(fields[0], errors='ignore'), "xbmc_id": int(fields[1]), "mbid": mbid }
        artists.append(artist)

    return artists

def GetThumbForArtistName(ArtistName):
    thumb = xbmc.getCacheThumbName('artist' + ArtistName)
    thumb = xbmc.translatePath("special://profile/Thumbnails/Music/Artists/%s" % thumb )
    
    print '%s -> %s' % (ArtistName, thumb)
    
    if not os.path.isfile(thumb):
        thumb = ''
        
    return thumb

def GetArtists():
    retval = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "id": 1 }')
    results = json.loads(retval)

    return results['result']['artists']

def GetSimiliarInLibrary(id):
    simi_artists = GetSimiliarById(id)
    xbmc_artists = GetXBMCArtists()

    artists = []
    
    start = time.clock()
    
    for (count, simi_artist) in enumerate(simi_artists):
        for (count, xbmc_artist) in enumerate(xbmc_artists):
            
            hit = False
            
            if xbmc_artist['mbid'] != '':
                #compare music brainz id
                if xbmc_artist['mbid'] == simi_artist['mbid']:
                    hit = True
            else:
                #compare names
                if xbmc_artist['name'] == simi_artist['name']:
                    hit = True
            
            if hit:
                xbmc_artist['thumb'] = GetThumbForArtistName(xbmc_artist['name'])
                artists.append(xbmc_artist)
    
    finish = time.clock()
            
    log('%i of %i artists found in last.FM is in XBMC database' % (len(artists), len(simi_artists)))
    log('Joining xbmc library and last.fm similiar artists took %f seconds' % (finish - start))
    xbmc.executebuiltin('Notification(Joining xbmc library and last.fm similiar artists,took %f seconds)' % (finish - start) )
    
    return artists    

def passDataToSkin(prefix, data):
    #use window properties
    wnd = xbmcgui.Window(10000)

    if data != None:
        wnd.setProperty('%s.Count' % prefix, str(len(data)))
        for (count, result) in enumerate(data):
            for (key,value) in result.iteritems():
                wnd.setProperty('%s.%i.%s' % (prefix, count + 1, str(key)), unicode(value))
    else:
        wnd.setProperty('%s.Count' % prefix, '0')

infos = []
Artist_mbid = None
AlbumName = None
TrackTitle = None
AdditionalParams = []

for arg in sys.argv:
    if arg == 'script.ExtraMusicInfo':
        continue
    
    param = arg.lower()
    
    if param.startswith('info='):
        infos.append(param[5:])
    
    elif param.startswith('artistname='):
        ArtistName = arg[11:]
        Artist_mbid = GetMusicBrainzId(ArtistName)
        
    elif param.startswith('albumname='):
        AlbumName = arg[10:]
        
    elif param.startswith('tracktitle='):
        TrackTitle = arg[11:]
        
    else:
        AdditionalParams.append(param)
        
for info in infos:
    if info == 'similiarartistsinlibrary':
        passDataToSkin('SimiliarArtists', None)
        artists = GetSimiliarInLibrary(Artist_mbid)
        passDataToSkin('SimiliarArtists', artists)
    
    elif info == 'artistsevents':
        passDataToSkin('MusicEvents', None)
        events = GetEvents(Artist_mbid)
        passDataToSkin('MusicEvents', events)
        
    elif info == 'updatexbmcdatabasewithartistmbidbg':
        
        SetMusicBrainzIDsForAllArtists(False, 'forceupdate' in AdditionalParams)
    elif info == 'updatexbmcdatabasewithartistmbid':
        SetMusicBrainzIDsForAllArtists(True, 'forceupdate' in AdditionalParams)
    
        '''
        wnd = xbmcgui.WindowDialog(xbmcgui.getCurrentWindowDialogId())
        ctrl= wnd.getControl(9999)
        items = []
        for art in arts:
            if art.has_key('thumb'):
                th =art['thumb']
            else:
                th = ''
                
                
            path = 'Dialog.Close(musicinformation) , ActivateWindow(MusicLibrary,musicdb://2/%i/)' % int(art['id'])
            item = xbmcgui.ListItem(art['name'], '', th, '', path)
            item.setPath(path)
            items.append(item)
            
        ctrl.setStaticContent(items)
        '''