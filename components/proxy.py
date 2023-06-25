from components.base import AS, AC, database, TooManyHopsError
from protocol.sip import Invite, Response, Bye, Ack

from copy import deepcopy
import logging


class Proxy(AS, AC):
    def __init__(self, addr):
        super().__init__(addr)

    @database('./data/aor.json')
    def process_request(self, request, data):
        if request.startswith("INVITE"):
            req = Invite().from_string(request)

        elif request.startswith("BYE"):
            req = Bye().from_string(request)

        elif request.startswith("ACK"):
            req = Ack().from_string(request)

        else:
            return data, None

        self.respond("100 Trying", deepcopy(req))

        if req.recipient_addr:
            try:
                self.send(deepcopy(req), req.recipient_addr)

            except TooManyHopsError:
                self.respond("483 Too Many Hops", deepcopy(req))

        elif addresses := data[req.recipient]:
            for address in addresses.keys():
                addr, port = address.split(':')

                try:
                    self.send(deepcopy(req), (addr, int(port)))

                except TooManyHopsError:
                    self.respond("483 Too Many Hops", deepcopy(req))

        else:
            self.respond("404 Not Found", deepcopy(req))

        return data, None

    def process_response(self, response):
        try:
            code = int(response.split()[0])

        except ValueError:
            raise ValueError("Failed to parse response!")

        else:
            if code != 100:
                response = Response.from_string(response)
                self.respond(response.code, response)
