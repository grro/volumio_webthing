import logging
import requests
import json
import time
from threading import Thread
from typing import List



class VolumioListener:

    def on_playing_updated(self, playing: bool):
        pass

    def on_artist_updated(self, artist: str):
        pass

    def on_title_updated(self, title: str):
        pass

    def on_favourite_stations_updated(self, stationnames: List[str]):
        pass

    def on_favourite_updated(self, stationname: str):
        pass



class Volumio(VolumioListener):

    def __init__(self, volumio_base_uri = 'http://10.1.33.30/api/v1/'):
        self.volumio_base_uri = volumio_base_uri
        self.__listener = VolumioListener()
        self.__playing = False
        self.__title = ""
        self.__artist = ""
        self.__favourites = []
        self.__favourite = {}
        self.sync_state()
        self.sync_favourites()
        Thread(target=self.__refresh_favourites_periodically, daemon=True).start()

    def __refresh_favourites_periodically(self):
        while True:
            try:
                time.sleep(15 * 60)
                self.sync_favourites()
            except Exception as e:
                print("error occurred by fetching favourites")

    def set_listener(self, listener: VolumioListener):
        self.__listener = listener

    @property
    def favourite_stations(self):
        return [favourite['title'] for favourite in self.__favourites]

    @property
    def favourite_station(self):
        return self.__favourite.get('title', "")

    @favourite_station.setter
    def favourite_station(self, station: str):
        self.play_favourite(station)

    @property
    def title(self):
        return self.__title

    @property
    def artist(self):
        return self.__artist

    @artist.setter
    def artist(self, artist: str):
        if artist != self.__artist:
            self.__artist = artist
            self.__listener.on_artist_updated(self.__artist)

    @property
    def playing(self):
        return self.__playing

    @playing.setter
    def playing(self, playing: bool):
        if playing:
            self.play()
        else:
            self.stop()
        self.on_playing_updated(playing)

    def on_playing_updated(self, playing: bool):
        if playing != self.__playing:
            self.__playing = playing
            self.__listener.on_playing_updated(self.__playing)

    def on_artist_updated(self, artist: str):
        if artist != self.artist:
            self.artist = artist
            self.__listener.on_artist_updated(self.artist)

    def on_title_updated(self, title: str):
        if title != self.__title:
            self.__title = title
            self.__listener.on_title_updated(self.__title)

    def on_favourites_updated(self, favourites):
        if favourites != self.__favourites:
            self.__favourites = favourites
            self.on_favourite_stations_updated([favourite['title'] for favourite in favourites])

    def on_favourite_stations_updated(self, stationnames: List[str]):
        self.__listener.on_favourite_stations_updated(stationnames)

    def on_favourite_updated(self, stationname: str):
        self.__listener.on_favourite_updated(stationname)


    def sync_state(self):
        response = requests.get(self.volumio_base_uri + '/api/v1/getstate')
        if response.status_code == 200:
            data = response.json()
            if 'status' in data.keys():
                self.on_playing_updated(data['status'] == 'play')
            if 'artist' in data.keys():
                self.on_artist_updated(data['artist'])
            if 'title' in data.keys():
                self.on_title_updated(data['title'])
        else:
            logging.warning("could not get state. Got " + response.text)

    def sync_favourites(self):
        response = requests.get(self.volumio_base_uri + '/api/v1/browse?uri=radio/favourites')
        if response.status_code == 200:
            favourites = response.json()['navigation']['lists'][0]['items']
            self.on_favourites_updated(favourites)
        else:
            logging.warning("could not get favourites. Got " + response.text)

    def is_success(self, response):
        if response.status_code == 200:
            j = response.json()
            if 'response' in j.keys() and 'success' in j['response'].lower():
                return True
        return False

    def play(self):
        response = requests.get(self.volumio_base_uri + "/api/v1/commands/?cmd=play")
        if self.is_success(response):
            logging.debug("start playing")
        else:
            logging.warning("could not start playing. Got " + response.text)

    def stop(self):
        response = requests.get(self.volumio_base_uri + "/api/v1/commands/?cmd=stop")
        if self.is_success(response):
            logging.debug("stop playing")
        else:
            logging.warning("could not stop playing. Got " + response.text)

    def play_favourite(self, station):
        for favourite in self.__favourites:
            if favourite['title'] == station:
                response = requests.post(self.volumio_base_uri + '/api/v1/replaceAndPlay', json.dumps(favourite), headers={'Content-Type': 'application/json'})
                if self.is_success(response):
                    logging.debug("playing station '" + station + "' ")
                else:
                    logging.warning("could set station " + station + ". Got " + response.text)
                return
        logging.warning("station " + station + " is unknown")

    def play_next_favourite(self):
        pass

    def play_previous_favourite(self):
        pass



volumio = Volumio('http://10.1.33.30:3000')

