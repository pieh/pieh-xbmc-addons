import simplejson as json
from Utils import log, GetStringFromUrl

bandsintown_apikey = 'xbmc_test'

def GetEvents(id):
    url = 'http://api.bandsintown.com/artists/mbid_%s/events?format=json&app_id=%s' % (id, bandsintown_apikey)
    response = GetStringFromUrl(url)
    results = json.loads(response)
    
    events = []
    
    for event in results:
        date = event['datetime']
        venue = event['venue']
        city = venue['city']
        name = venue['name']
        region = venue['region']
        country = venue['country']
        
        event = {'date': date, 'city': city, 'name':name, 'region':region, 'country':country  }
        events.append(event)
        
    return events