from protocol import sip

from random import randint
from socket import socket, AF_INET, SOCK_DGRAM
from collections import defaultdict
from json import load, dump


class TooManyHopsError(BaseException):
    pass


def database(path):
    def wrapper(func):
        def wrap(*args, **kwargs):
            with open(path, 'r') as f:
                data = defaultdict(dict, load(f))

            new_data, result = func(*args, data, **kwargs)

            with open(path, 'w') as f:
                dump(new_data, f)

            return result

        return wrap
    return wrapper


class AC:
    def __init__(self, addr):
        self.addr = addr
        self.sock = socket(AF_INET, SOCK_DGRAM)

    def send(self, request, addr):
        request.via.append((self.addr, f"z9hG4bK{randint(0, 1000000000000000)}"))
        request.max_forwards -= 1

        if request.max_forwards <= 0:
            raise TooManyHopsError()

        self.sock.sendto(bytes(request), addr)


class AS:
    def __init__(self, addr):
        self.addr = addr
        self.sock = socket(AF_INET, SOCK_DGRAM)

    def respond(self, response, request):
        addr, branch = request.via.pop(0)

        re = sip.Response()
        re.code = response
        re.value = request.response_headers()

        self.sock.sendto(bytes(re), addr)
