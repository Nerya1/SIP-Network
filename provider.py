from socket import socket, AF_INET, SOCK_DGRAM
from datetime import datetime

from components.registrar import Registrar
from components.proxy import Proxy

import logging
logging.basicConfig(
    filename=f'./logs/provider-{datetime.now()}.log',
    filemode='w',
    format='[%(asctime)s] %(message)s',
    level=logging.DEBUG
)


class Provider:
    def __init__(self, addr):
        self.proxy = Proxy(addr)
        self.registrar = Registrar(addr, 3600)

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(addr)

        self.last_serve = datetime.now()

    def get_request(self):
        data, addr = self.sock.recvfrom(1024)
        data = data.decode()

        return data

    def handle_request(self, data):
        # let registrar try handle request
        try:
            self.registrar.process_request(data)

        except ValueError:
            pass

        else:
            logging.info("request handled by registrar!")

        # let proxy try handle request
        try:
            self.proxy.process_request(data)

        except ValueError:
            pass

        else:
            logging.info("request handled by proxy!")

        # let proxy try handle response
        try:
            self.proxy.process_response(data)

        except ValueError:
            pass

        else:
            logging.info("response handled by proxy!")

    def serve(self):
        data = self.get_request()

        logging.info("data received!")
        logging.debug(data)

        time = datetime.now()

        dt = (time - self.last_serve).microseconds / 1000000

        timed_out = self.registrar.timeout(dt)
        logging.debug(f"elapsed timeout by {dt} seconds!")

        for client in timed_out:
            logging.info(f"timed out {client}!")

        self.last_serve = time

        self.handle_request(data)

    def run(self):
        while True:
            self.serve()


if __name__ == '__main__':
    addr = input("addr? [eg. 127.0.0.1:6500] ").split(':')

    provider = Provider((addr[0], int(addr[1])))
    provider.run()
