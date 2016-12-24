#!bin/python
from flask import Flask, jsonify
from fuzzywuzzy import process, fuzz
import requests, json, re

app = Flask(__name__)

KODI='<KODI_IP>:8080'
USER='kodi'
PW='KODI_API_PASSWORD'

def update_movies():
    library = requests.get('http://%s/jsonrpc?request={"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "ascending", "method": "label", "ignorearticle": true } }, "id": "libMovies"}' % KODI, auth=(USER, PW))
    return library.text

def update_tv():
    library = requests.get('http://%s/jsonrpc?request={"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "ascending", "method": "label", "ignorearticle": true } }, "id": "libTV"}' % KODI, auth=(USER, PW))
    return library.text

def get_episodes_for_show(tvshowid):
    library = requests.get('http://%s/jsonrpc?request={"jsonrpc":"2.0", "method": "VideoLibrary.GetEpisodes", "id": 1, "params": { "properties":["season", "episode", "tvshowid"], "tvshowid": %s , "sort": {"order": "descending", "method": "lastplayed"}}}' % (KODI, tvshowid), auth=(USER, PW) )
    return library.text

def get_season(season, tvshowid):
    library = requests.get('http://%s/jsonrpc?request={"jsonrpc":"2.0", "method": "VideoLibrary.GetEpisodes", "id": 1, "params": { "properties":["season", "episode", "tvshowid"], "tvshowid": %s , "season": %d, "sort": {"order": "descending", "method": "lastplayed"}}}' % (KODI, tvshowid, int(season)), auth=(USER, PW) )
    return library.text

def play_movie(movieid):
    req = requests.get('http://%s/jsonrpc?request={"jsonrpc": "2.0", "params": {"item": {"movieid": %s}}, "method": "Player.Open", "id": 1}' % (KODI, movieid), auth=(USER, PW))

def play_episode(episodeid):
    req = requests.get('http://%s/jsonrpc?request={"jsonrpc": "2.0", "params": {"item": {"episodeid": %s}}, "method": "Player.Open", "id": 1}' % (KODI, episodeid), auth=(USER, PW))


@app.route('/movie/<string:title>', methods=['GET'])
def process_movie(title):
    movies  =  json.loads(update_movies())
    titles = tuple([(movie['label'], movie['movieid']) for movie in movies['result']['movies']])
    match = process.extractOne(title, titles, scorer=fuzz.token_sort_ratio)
    play_movie(match[0][1])
    return match[0]

@app.route('/tv/<string:title>', methods=['GET'])
def process_tv(title):
    shows  =  json.loads(update_tv())
    titles = tuple([(show['label'], show['tvshowid']) for show in shows['result']['tvshows']])
    show, season, episode = re.compile('season|episode', re.IGNORECASE).split(title)
    show_match = process.extractOne(show.strip(), titles, scorer=fuzz.token_sort_ratio)
    season_lib = json.loads(get_season(season, show_match[0][1]))   
    ep_id = [ep['episodeid'] for ep in season_lib['result']['episodes'] if ep['episode'] == int(episode)]
    play_episode(str(ep_id[0]))
    return show_match[0]
    
if __name__ == '__main__':
    app.run(debug=True, host= '0.0.0.0')



#TODO Add support to simply say a show name and play a random episode for that show. Support for a random movies as well.
