from protocol.sip import Register, Invite, Bye
from components.base import AC

from datetime import datetime


class UAC(AC):
    def __init__(self, addr, aor):
        super().__init__(addr)

        self.aor = aor

    def register(self, registrar):
        req = Register()

        req.aor = self.aor
        req.expires = 3600
        req.call_id = f"{datetime.now()}-{self.addr[0]}:{self.addr[1]}"
        req.recipient = registrar
        req.max_forwards = 2
        req.sender_addr = self.addr
        req.cseq = 1

        self.send(req, registrar)

    def invite(self, proxy, recipient):
        req = Invite()

        req.recipient = recipient
        req.sender = self.aor
        req.max_forwards = 5
        req.call_id = f"{datetime.now()}-{self.addr[0]}:{self.addr[1]}"
        req.content_type = "application/sdp"
        req.sender_addr = self.addr
        req.cseq = 1
        req.content = "NOT IMPLEMENTED"

        self.send(req, proxy)

    def bye(self, proxy, recipient):
        req = Bye()
        req.recipient = recipient
        req.sender = self.aor
        req.max_forwards = 5
        req.call_id = f"{datetime.now()}-{self.addr[0]}:{self.addr[1]}"
        req.content_type = "application/sdp"
        req.sender_addr = self.addr
        req.cseq = 1
        req.content = "NOT IMPLEMENTED"

        self.send(req, proxy)
