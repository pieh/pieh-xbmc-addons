import xbmc,xbmcgui
import urllib
import xml.dom.minidom
import simplejson as json
import re
import time
import xbmcplugin
import os

from MusicBrainz import GetMusicBrainzId, SetMusicBrainzIDsForAllArtists
from BandsInTown import GetEvents, GetNearEvents
from Lastfm import GetSimiliarById
from Utils import log, GetStringFromUrl, GetValue, GetAttribute, Notify
import xbmcaddon

def GetXBMCArtists():
    sqlQuery = "SELECT DISTINCT artist.strArtist, song.idArtist, song.strMusicBrainzArtistID FROM song JOIN artist ON artist.idArtist=song.idArtist ORDER BY COUNT(song.idSong) DESC"
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
    
    if not os.path.isfile(thumb):
        thumb = ''
        
    print '%s -> %s' % (ArtistName, thumb)
        
    return thumb

'''
def GetArtists():
    retval = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "id": 1 }')
    results = json.loads(retval)

    return results['result']['artists']
'''
def GetSimiliarInLibrary(id):
    simi_artists = GetSimiliarById(id)
    if simi_artists == None:
         Notify('Last.fm didn\'t return proper response - check debug log for more details')
         return None
    
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
    Notify('Joining xbmc library and last.fm similiar artists', 'took %f seconds)' % (finish - start))
    
    return artists    

def passDataToSkin(prefix, data):
    #use window properties
    wnd = xbmcgui.Window(Window)

    if data != None:
        wnd.setProperty('%s.Count' % prefix, str(len(data)))
        log( "%s.Count = %s" % (prefix, str(len(data)) ) )
        for (count, result) in enumerate(data):
            log( "%s.%i = %s" % (prefix, count + 1, str(result) ) )
            for (key,value) in result.iteritems():
                wnd.setProperty('%s.%i.%s' % (prefix, count + 1, str(key)), unicode(value))
    else:
        wnd.setProperty('%s.Count' % prefix, '0')

infos = []
Artist_mbid = None
AlbumName = None
TrackTitle = None
AdditionalParams = []
Window = 10000

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
    
    elif param.startswith('window='):
        Window = int(arg[7:])
    
    elif param.startswith('settuplocation'):
        settings = xbmcaddon.Addon(id='script.ExtraMusicInfo')
        country = settings.getSetting('country')
        city = settings.getSetting('city')
        
        log('stored country/city: %s/%s' % (country, city) )  
        
        kb = xbmc.Keyboard('', 'Country:')
        kb.doModal()
        country = kb.getText()
        
        kb = xbmc.Keyboard('', 'City:')
        kb.doModal()
        city = kb.getText()
        
        log('country/city: %s/%s' % (country, city) )         
        
        settings.setSetting('location_method', 'country_city')
        settings.setSetting('country',country)
        settings.setSetting('city',city)
        
        log('done with settings')
    
    else:
        AdditionalParams.append(param)

passDataToSkin('SimiliarArtists', None)
passDataToSkin('MusicEvents', None)

for info in infos:
    if info == 'similiarartistsinlibrary':
        artists = GetSimiliarInLibrary(Artist_mbid)
        passDataToSkin('SimiliarArtistsInLibrary', artists)
    
    elif info == 'artistevents':
        events = GetEvents(Artist_mbid)
        passDataToSkin('ArtistEvents', events)
    
    elif info == 'nearevents':
        events = GetNearEvents()
        passDataToSkin('NearEvents', events)        
    
    elif info == 'topartistsnearevents':
        artists = GetXBMCArtists()
        
        events = GetNearEvents(artists[0:15])
        passDataToSkin('TopArtistsNearEvents', events)
        
    elif info == 'updatexbmcdatabasewithartistmbidbg':
        SetMusicBrainzIDsForAllArtists(False, 'forceupdate' in AdditionalParams)
    elif info == 'updatexbmcdatabasewithartistmbid':
        SetMusicBrainzIDsForAllArtists(True, 'forceupdate' in AdditionalParams)
