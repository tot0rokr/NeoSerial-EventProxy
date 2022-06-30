from multiprocessing.connection import Client

class EventProxyClient(object):
    def __init__(self, address=('localhost', 5080)):
        self.address = address

    def __call__(self, op, *args, **kwargs):
        with Client(self.address, authkey=b'5678') as conn:
            conn.send((op, args, kwargs))
            ret = conn.recv()
        return ret

