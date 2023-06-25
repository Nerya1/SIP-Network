from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
from queue import Empty

from components.user_agent_server import UAS
from components.user_agent_client import UAC


import logging
logging.basicConfig(
    filename=f'./logs/user-{datetime.now()}.log',
    filemode='w',
    format='[%(asctime)s] %(message)s',
    level=logging.DEBUG
)


class Client:
    def __init__(self, addr, proxy,  aor):
        self.server = UAS(addr)
        self.client = UAC(addr, aor)
        self.proxy = proxy

        self.running = Future()
        self.thread_pool = ThreadPoolExecutor(max_workers=1)

    def register(self):
        self.client.register(self.proxy)

        try:
            while (status := self.server.message_queue.get(timeout=3)) not in ("200 OK", "501 Not Implemented"):
                pass

        except Empty:
            print("Failed to connect to server!")

        else:
            match status:
                case "200 OK":
                    print("Successfully registered!")

                case "501 Not Implemented":
                    print("Binding multiple clients to a single AOR not supported!")
                    self.running.cancel()

                case _:
                    print("Unknown response from server!")
                    self.running.cancel()

    def serve(self):
        if not self.running.done():
            self.thread_pool.submit(self.serve)

        if not (data := self.server.get_request()):
            return

        # log data received
        logging.info("data received!")
        logging.debug(data)

        # try handle response
        if self.server.handle_response(data):
            logging.info("response handled!")

        # try handle request
        response, request = self.server.handle_request(data)

        if response:
            self.server.respond(response, request)

            logging.info("response sent!")
            logging.debug(response)

    def run(self):
        print('Commands: exit, call, status, register, bye')
        self.thread_pool.submit(self.serve)
        self.register()

        while not self.running.done():
            match input('> '):
                case 'exit':
                    self.running.cancel()

                case 'call':
                    recipient = input('recipient? ')
                    self.client.invite(self.proxy, recipient)

                    self.server.call["other"] = recipient
                    self.server.call["sdp"] = 'NOT IMPLEMENTED'

                    try:
                        while (status := self.server.message_queue.get(timeout=3)) != '180 Ringing':
                            pass

                    except Empty:
                        status = None

                    if status == "180 Ringing":
                        print("Call accepted!")

                    else:
                        print("Call declined!")

                case 'status':
                    print(self.server.call)

                case 'register':
                    self.register()

                case 'bye':
                    if not self.server.call["ongoing"]:
                        print("You are not currently in a call!")

                    else:
                        self.client.bye(self.proxy, self.server.call["other"])
                        self.server.call["ongoing"] = False
                        print("Call hung up successfully")


if __name__ == '__main__':
    name = input('username? ')
    addr = input("address? [eg 127.0.0.1:6500] ").split(':')
    proxy = input("proxy? ").split(':')

    client = Client((addr[0], int(addr[1])), (proxy[0], int(proxy[1])), name)
    client.run()
