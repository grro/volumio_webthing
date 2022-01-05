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

    def on_albumart_updated(self, albumart_uri):
        pass



class Volumio(VolumioListener):

    def __init__(self, volumio_base_uri: str):
        if volumio_base_uri.endswith("/"):
            self.volumio_base_uri = volumio_base_uri
        else:
            self.volumio_base_uri = volumio_base_uri + "/"
        self.__listener = VolumioListener()
        self.__playing = False
        self.__title = ""
        self.__artist = ""
        self.__albumart = ""
        self.__favourites = []
        self.__favourite = {}

        logging.info("connecting volumio server " + volumio_base_uri)
        self.sync_state()
        self.sync_favourites()
        Thread(target=self.__refresh_favourites_periodically, daemon=True).start()

    def __refresh_favourites_periodically(self):
        while True:
            try:
                time.sleep(5 * 60)
                self.sync_favourites()
            except Exception as e:
                logging.error("error occurred by fetching favourites")

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
    def albumart(self):
        return self.__albumart

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

    def on_albumart_updated(self, albumart):
        if albumart != self.__albumart:
            self.__albumart = albumart
            self.__listener.on_albumart_updated(albumart)

    def sync_state(self):
        response = requests.get(self.volumio_base_uri + 'api/v1/getstate')
        if response.status_code == 200:
            data = response.json()
            if 'status' in data.keys():
                self.on_playing_updated(data['status'] == 'play')
            if 'artist' in data.keys():
                self.on_artist_updated(data['artist'])
            if 'title' in data.keys():
                self.on_title_updated(data['title'])
            albumart = data.get('albumart', '')
            if albumart.startswith("/"):
                albumart = self.volumio_base_uri[:-1] + albumart
            self.on_albumart_updated(albumart)
        else:
            logging.warning("could not get state. Got " + response.text)

    def sync_favourites(self):
        response = requests.get(self.volumio_base_uri + 'api/v1/browse?uri=radio/favourites')
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
        response = requests.get(self.volumio_base_uri + "api/v1/commands/?cmd=play")
        if self.is_success(response):
            logging.info("start playing")
            self.sync_state()
        else:
            logging.warning("could not start playing. Got " + response.text)

    def stop(self):
        response = requests.get(self.volumio_base_uri + "api/v1/commands/?cmd=stop")
        if self.is_success(response):
            logging.info("stop playing")
            self.sync_state()
        else:
            logging.warning("could not stop playing. Got " + response.text)

    def play_favourite(self, station_to_play) -> bool:
        station = None

        # exact match
        for favourite in self.__favourites:
            if favourite['title'].strip().lower() == station_to_play.lower():
                station = favourite
                break

        # approximately match
        if station is None:
            for favourite in self.__favourites:
                if favourite['title'].strip().lower().startswith(station_to_play.lower()):
                    station = favourite
                    break

        # play station
        if station is None:
            logging.warning("station " + station_to_play + " is unknown")
        else:
            uri = self.volumio_base_uri + 'api/v1/replaceAndPlay'
            payload = json.dumps({'item': station})
            response = requests.post(uri, payload, headers={'Content-Type': 'application/json'})
            if self.is_success(response):
                logging.info("playing station '" + station_to_play + "' ")
                self.sync_state()
                return True
            else:
                logging.warning("could set station " + station_to_play + ". Got " + response.text)
        return False


'''
if __name__ == "__main__":
    voluimo_url = sys.argv[1]
    volumio = Volumio(voluimo_url)
    print(volumio.favourite_stations)
    print(volumio.play_favourite("Swr3"))
    print(volumio.play_favourite("Beats"))
'''