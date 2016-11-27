import threading
from queue import Queue

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/callback')
def app_route_callback():
    OAuthCallbackServer.callback_url_queue.put(request.url)
    return 'ok'


@app.route('/ping')
def app_route_ping():
    return 'ok'


@app.route('/shutdown')
def app_route_shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return ''


class OAuthCallbackServer(object):

    callback_url_queue = None

    def __init__(self, host='localhost', port=7777):
        self.host = host
        self.port = port

    def wait_for_callback_url(self):
        return OAuthCallbackServer.callback_url_queue.get()

    def start(self):
        OAuthCallbackServer.callback_url_queue = Queue()

        t = threading.Thread(target=self.start_threaded,
                             args=(self.host, self.port))
        t.daemon = True
        t.start()

        # Ping the server until it's ready
        ping_url = "http://%s:%s/ping" % (self.host, self.port)
        while True:
            try:
                requests.get(ping_url, timeout=0.5)
                return
            except requests.exceptions.ConnectionError:
                pass

    def start_threaded(self, host, port):
        app.run(
          host=host,
          port=port
        )

    def stop(self):
        shutdown_url = "http://%s:%s/shutdown" % (self.host, self.port)
        requests.get(shutdown_url)
