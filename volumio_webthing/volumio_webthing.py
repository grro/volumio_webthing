from webthing import (SingleThing, Property, Thing, Value, WebThingServer)
from volumio import Volumio, VolumioListener
from volumio_event_receiver import run_event_listener
from typing import List
import tornado.ioloop
import logging



class VolumioThing(Thing, VolumioListener):

    def __init__(self, description: str, volumio: Volumio):
        Thing.__init__(
            self,
            'urn:dev:ops:volumio-1',
            'Volumio',
            [],
            description
        )

        self.volumio = volumio
        volumio.set_listener(self)

        self.playing = Value(volumio.playing, self.__playing)
        self.add_property(
            Property(self,
                     'playing',
                     self.playing,
                     metadata={
                         '@type': 'BooleanProperty',
                         'title': 'playing',
                         'type': 'boolean',
                         'description': 'true, is playing',
                         'readOnly': False
                     }))

        self.artist = Value(volumio.artist)
        self.add_property(
            Property(self,
                     'artist',
                     self.artist,
                     metadata={
                         'title': 'artist',
                         'type': 'string',
                         'description': 'the artist',
                         'readOnly': True
                     }))

        self.song_title = Value(volumio.title)
        self.add_property(
            Property(self,
                     'title',
                     self.song_title,
                     metadata={
                         'title': 'title',
                         'type': 'string',
                         'description': 'the title',
                         'readOnly': True
                     }))

        self.favourite_station = Value(volumio.favourite_station, self.__favourite_station)
        self.add_property(
            Property(self,
                     'favourite_station',
                     self.favourite_station,
                     metadata={
                         'title': 'favourite station',
                         'type': 'string',
                         'description': 'the favourite station',
                         'readOnly': False
                     }))

        self.favourite_stations = Value("\n".join(volumio.favourite_stations))
        self.add_property(
            Property(self,
                     'favourite_stations',
                     self.favourite_stations,
                     metadata={
                         'title': 'favourite stations',
                         'type': 'string array',
                         'description': 'the favourite stations',
                         'readOnly': True
                     }))

        self.ioloop = tornado.ioloop.IOLoop.current()


    def on_artist_updated(self, artist):
        self.ioloop.add_callback(self.__update_artist, artist)

    def __update_artist(self, artis):
        self.artist.notify_of_external_update(artis)

    def on_title_updated(self, title):
        self.ioloop.add_callback(self.__update_title, title)

    def __update_title(self, title):
        self.song_title.notify_of_external_update(title)

    def __playing(self, playing: bool):
        self.volumio.playing = playing

    def on_playing_updated(self, playing: bool):
        self.ioloop.add_callback(self.__update_playing, playing)

    def __update_playing(self, playing: bool):
        self.playing.notify_of_external_update(playing)

    def on_favourite_stations_updated(self, stations: List[str]):
        self.ioloop.add_callback(self.__update_favourite_stations, stations)

    def __update_favourite_stations(self, stations: List[str]):
        self.favourite_stations.notify_of_external_update("\n".join(stations))

    def on_favourite_updated(self, stationname: str):
        self.ioloop.add_callback(self.__update_favourite_stationname, stationname)

    def __update_favourite_stationname(self, stationname: str):
        self.favourite_station.notify_of_external_update(stationname)

    def __favourite_station(self, favourite_station: str):
        self.volumio.favourite_station = favourite_station



def run_server(port: int, description, volumio_base_uri, event_listener_port: int):
    volumio = Volumio(volumio_base_uri)
    volumio_webthing = VolumioThing(description, volumio)
    server = WebThingServer(SingleThing(volumio_webthing), port=port, disable_host_validation=True)

    # start volumio event listener
    run_event_listener(volumio, volumio_base_uri, event_listener_port)

    try:
        # start webthing server
        logging.info('starting the server listing on ' + str(port))
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping the server')
        server.stop()
        logging.info('done')



run_server(9070, "test", 'http://10.1.33.30:3000', 9090)