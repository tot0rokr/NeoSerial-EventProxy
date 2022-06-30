import sys
import logging

if sys.version_info < (3, 7):
    print(("ERROR: To use {} you need at least Python 3.7.\n" +
           "You are currently using Python {}.{}").format(sys.argv[0], *sys.version_info))
    sys.exit(1)

import threading
from multiprocessing.connection import Listener
from queue import Queue

from nrf_sdk.serial_api.runtime.mesh_api_client import MeshAPIClient
import serial_app
from importlib import reload

logging.basicConfig(level=logging.INFO)

class EventProxyServer(object):
    def __init__(self, address=('localhost', 5080), api_address=('localhost', 5070)):
        self.address  = address
        self.listener = threading.Thread(target=self.listener_runner)
        self.worker   = threading.Thread(target=self.worker_runner)
        self.queue    = Queue()
        self.api      = MeshAPIClient(api_address)
        self.listener.start()
        self.worker.start()

    def listener_runner(self):
        with Listener(self.address, authkey=b'5678') as listener:
            while True:
                conn = listener.accept()
                conn_addr = listener.last_accepted
                data = conn.recv()
                logging.info("%s:%d - %s - %s", conn_addr[0], conn_addr[1], data[0], data[1])

                self.queue.put((conn, *data))

    def worker_runner(self):
        while True:
            conn, op, args, kwargs = self.queue.get()
            logging.info("run     : %s - %s", op, args[0])
            try:
                result = self.event_handler(op, *args, **kwargs)
            except Exception as e:
                result = str(e)
                logging.error("%s", e)
            logging.info("finished: %s - %s", op, args[0])
            conn.send(result)
            conn.close()

    def event_handler(self, op, *args, **kwargs):
        if op == 'api':
            return self.api(*args, **kwargs)
        elif op == 'app':
            func_name = args[0]
            args = args[1:]
            if not hasattr(serial_app, func_name):
                reload(serial_app)
            app = getattr(serial_app, func_name)
            return app(self.api, *args, **kwargs)
        elif op == 'db':
            pass
        else:
            print("EventProxyServer:Unknown Operation: {} {} {}".format(op, args, kwargs))
        return None
