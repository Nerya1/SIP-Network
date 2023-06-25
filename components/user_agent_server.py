from copy import deepcopy
from socket import socket, AF_INET, SOCK_DGRAM
from select import select
from queue import Queue

from components.base import AS
from protocol.sip import Invite, Response, Bye


class UAS(AS):
    def __init__(self, addr):
        super().__init__(addr)

        self.server_socket = socket(AF_INET, SOCK_DGRAM)
        self.server_socket.bind(addr)

        self.addr = addr
        self.call = {"ongoing": False, "other": None, "sdp": None}
        self.message_queue = Queue()

    def handle_request(self, data):
        if data.startswith("INVITE"):
            invite = Invite().from_string(data)

            if self.call["ongoing"]:
                return "486 Busy Here", deepcopy(invite)

            invite.recipient_addr = self.addr
            self.call["ongoing"] = True
            self.call["other"] = invite.sender
            self.call["sdp"] = invite.content

            return "180 Ringing", deepcopy(invite)

        if data.startswith("BYE"):
            bye = Bye().from_string(data)

            if bye.sender == self.call["other"]:
                self.call["ongoing"] = False

            return "200 OK", deepcopy(bye)

        return None, None

    def handle_response(self, data):
        response = False

        if data.split(' ')[0].isdigit():
            response = Response.from_string(data)
            self.message_queue.put(response.code)

            if response.code in ('486 Busy Here', '404 Not Found'):
                self.call["ongoing"] = False

            if response.code == '180 Ringing':
                if self.call["ongoing"]:
                    self.respond("486 Busy Here", response)

                self.call["ongoing"] = True

        return response

    def get_request(self):
        read, write, err = select([self.server_socket], [], [], 0.1)

        if self.server_socket not in read:
            return False

        data, addr = self.server_socket.recvfrom(1024)
        data = data.decode()

        return data
