from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from volumio_webthing.volumio import VolumioListener
import requests
import json
import logging
import threading



class EventHandler(BaseHTTPRequestHandler):

    handler = None

    def do_POST(self):
        try:
            try:
                body = self.rfile.read(int(self.headers.get('content-length', 0))).decode("utf-8")
                j = json.loads(body)
                if j['item'] == 'state':
                    self.handler.handle_state(j['data'])
                elif j['item'] == 'queue':
                    pass
                else:
                    print("UNKOWN EVENT " + body)
            except Exception as e:
                print(e)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        except Exception as e:
            logging.warning(e)



class StateHandler:

    def __init__(self, listener: VolumioListener):
        self.listener = listener
        self.status = ""
        self.artist = ""
        self.title = ""

    def handle_state(self, data):
        status = data.get('status', '')
        if status != self.status:
            self.status = status
            playing = status == 'play'
            self.listener.on_playing_updated(playing)
        artist = data.get('artist', '')
        if artist != self.artist:
            self.artist = artist
            self.listener.on_artist_updated(artist)
        title = data.get('title', '')
        if title != self.title:
            self.title = title
            self.listener.on_title_updated(title)



class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass


def register(volumio_uri: str, listen_port: int):
    if not volumio_uri.endswith("/"):
        volumio_uri = volumio_uri + "/"
    response = requests.post(volumio_uri + "api/v1/pushNotificationUrls",
                             data=json.dumps({"url": "http://localhost:" + str(listen_port)}), headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        logging.debug("listener registered " + response.text)
    else:
        logging.warning("could not register listener. Got " + response.text)


def run(listener: VolumioListener, volumio_base_uri: str, listen_port: int):
    register(volumio_base_uri, listen_port)

    EventHandler.handler = StateHandler(listener)
    server = ThreadingSimpleServer(('0.0.0.0', listen_port), EventHandler)
    print("event server listening on " + str(listen_port))
    server.serve_forever()


def run_event_listener(listener: VolumioListener, volumio_base_uri: str, listen_port: int):
    threading.Thread(target=run, args=(listener, volumio_base_uri, listen_port)).start()



