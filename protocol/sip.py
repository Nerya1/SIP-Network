from protocol.meta import Packet


class Address:
    def __init__(self, data=""):
        self.address, self.seperator, self.tag = data.partition(';tag=')

    def __repr__(self):
        return f"{self.address}{self.seperator}{self.tag}"


class List:
    def __init__(self, data=""):
        self.values = data.split(', ')

    def __repr__(self):
        return ', '.join(self.values)


class Invite(metaclass=Packet):
    recipient = "INVITE {} SIP/2.0", Address
    path = "Via: SIP/2.0/UDP {}", Address
    sender_full = "From: {}", Address
    recipient_full = "To: {}", Address
    call_id = "Call-ID: {}", str
    cseq = "CSeq: {} INVITE", int
    user_agent = "User-Agent: {}", str
    expires = "Expires: {}", int
    accept = "Accept: {}", str
    content_type = "Content-Type: {}", str
    content_length = "Content-Length: {}", int
    contact = "Contact: {}", Address
    max_forwards = "Max-Forwards: {}", int
    allow = "Allow: {}", List
