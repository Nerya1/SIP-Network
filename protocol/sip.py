import re


# --- taken from stack overflow ---

def string_to_dict(string, pattern):
    regex = re.sub(r'{(.+?)}', r'(?P<_\1>.+)', pattern)
    values = list(re.search(regex, string).groups())
    keys = re.findall(r'{(.+?)}', pattern)
    _dict = dict(zip(keys, values))
    return _dict

# ---------------------------------


class Invite:
    def __init__(self):
        self.recipient = ""  # AoR of recipient
        self.sender = ""  # AoR of sender
        self.via = []  # stack of (address, branch) tuples
        self.max_forwards = 0  # max forwards allowed to reach the recipient
        self.call_id = ""  # call id
        self.content_type = ""  # content type
        self.content = ""  # the invite's content
        self.sender_addr = ""  # the address of the original sender
        self.recipient_addr = ""  # the address of the recipient
        self.cseq = 0

    def __str__(self):
        invite = f"INVITE {self.recipient} SIP/2.0\r\n"
        invite += ''.join(f"Via: SIP/2.0/UDP {':'.join(map(str, address))};branch={branch}\r\n" for address, branch in self.via[::-1])
        invite += f"Max-Forwards: {self.max_forwards}\r\n"
        invite += f"From: <sip:{self.sender}>" + (f";tag={':'.join(map(str, self.sender_addr))}\r\n" if self.sender_addr else "\r\n")
        invite += f"To: <sip:{self.recipient}>" + (f";tag={':'.join(map(str, self.recipient_addr))}\r\n" if self.recipient_addr else "\r\n")
        invite += f"Call-ID: {self.call_id}\r\n"
        invite += f"CSeq: {self.cseq} INVITE\r\n"
        invite += f"Contact: sip:{self.sender}\r\n"
        invite += f"Content-Type: {self.content_type}\r\n" if self.content_type else ""
        invite += f"Content-Length: {len(self.content)}\r\n\r\n"
        invite += self.content

        return invite

    def __bytes__(self):
        return str(self).encode()

    def response_headers(self):
        invite = ''.join(f"Via: SIP/2.0/UDP {':'.join(map(str, address))};branch={branch}\r\n" for address, branch in self.via[::-1])
        invite += f"Max-Forwards: {self.max_forwards}\r\n"
        invite += f"From: <sip:{self.sender}>" + f";tag={':'.join(map(str, self.sender_addr))}\r\n" if self.sender_addr else "\r\n"
        invite += f"To: <sip:{self.recipient}>" + f";tag={':'.join(map(str, self.recipient_addr))}\r\n" if self.recipient_addr else "\r\n"
        invite += f"Call-ID: {self.call_id}\r\n"
        invite += f"CSeq: {self.cseq} INVITE\r\n"
        invite += f"Contact: sip:{self.sender}\r\n"
        invite += f"Content-Length: 0\r\n\r\n"

        return invite

    def from_string(self, invite):
        headers, body = invite.split("\r\n\r\n")
        headers = headers.split("\r\n")

        for header in headers:
            header = header.split(" ")
            header = [header[0], " ".join(header[1:])]

            match header:
                case ["Contact:", params]:
                    pass

                case ["INVITE", params]:
                    self.recipient = string_to_dict(params, '{recipient} SIP/2.0')["recipient"]

                case ["BYE", params]:
                    self.recipient = string_to_dict(params, '{recipient} SIP/2.0')['recipient']

                case ["ACK", params]:
                    self.recipient = string_to_dict(params, '{recipient} SIP/2.0')["recipient"]

                case ["Via:", params]:
                    addr, branch = string_to_dict(params, "SIP/2.0/UDP {address};branch={branch}").values()
                    addr = addr.split(':')
                    addr[1] = int(addr[1])

                    self.via.append((tuple(addr), branch))

                case ["Max-Forwards:", params]:
                    self.max_forwards = int(params)

                case ["From:", params]:
                    if ";tag=" in params:
                        tmp = string_to_dict(params, "<sip:{sender}>;tag={tag}")
                        self.sender_addr = tuple(tmp["tag"].split(':'))

                    else:
                        tmp = string_to_dict(params, "<sip:{sender}>")

                    self.sender = tmp["sender"]

                case ["To:", params]:
                    if ";tag=" in params:
                        tmp = string_to_dict(params, "<sip:{recipient}>;tag={tag}")
                        self.recipient_addr = tuple(tmp["tag"].split(':'))

                    else:
                        tmp = string_to_dict(params, "<sip:{recipient}>")

                    self.recipient = tmp["recipient"]

                case ["Call-ID:", params]:
                    self.call_id = params

                case ["CSeq:", params]:
                    self.cseq = int(params.split()[0])

                case ["Content-Type:", params]:
                    self.content_type = params

                case ["Content-Length:", params]:
                    pass

                case _:
                    raise ValueError(f"Failed to parse header \"{header}\"!")

        self.content = body
        return self


# I really should have done this differently but redoing my protocol would take too long
class Bye(Invite):
    def __str__(self):
        return ' '.join(["BYE", *super().__str__().split(' ')[1:]])


class Ack(Invite):
    def __str__(self):
        return ' '.join(["ACK", *super().__str__().split(' ')[1:]])


class Response:
    def __init__(self):
        self.code = ""
        self.via = []
        self.value = ""

    @staticmethod
    def from_string(response):
        ret = Response()
        code, *headers = response.split('\r\n')

        ret.code = code

        for header in headers:
            if header.startswith('Via:'):
                addr, branch = string_to_dict(header, "Via: SIP/2.0/UDP {address};branch={branch}").values()
                addr = addr.split(':')
                addr[1] = int(addr[1])

                ret.via.append((tuple(addr), branch))

            else:
                ret.value += f'{header}\r\n'

        ret.value += '\r\n'

        return ret

    def response_headers(self):
        headers = ''
        headers += ''.join(f"Via: SIP/2.0/UDP {':'.join(map(str, address))};branch={branch}\r\n" for address, branch in self.via[::-1])
        headers += self.value

        return headers

    def __str__(self):
        response = f"{self.code}\r\n"
        response += ''.join(f"Via: SIP/2.0/UDP {':'.join(map(str, address))};branch={branch}\r\n" for address, branch in self.via[::-1])
        response += self.value

        return response

    def __bytes__(self):
        return str(self).encode()


class Register:
    def __init__(self):
        self.aor = ""
        self.via = []
        self.sender_addr = ""
        self.call_id = ""
        self.recipient = ""
        self.expires = 0
        self.max_forwards = 0
        self.recipient = ""
        self.recipient_addr = ""
        self.cseq = 0
        self.content = ""

    def from_string(self, register):
        headers, body = register.split("\r\n\r\n")
        headers = headers.split("\r\n")

        for header in headers:
            header = header.split(" ")
            header = [header[0], " ".join(header[1:])]

            match header:
                case ["REGISTER", params]:
                    self.sender_addr = string_to_dict(params, 'sip:{sender_addr} SIP/2.0')["sender_addr"]
                    self.sender_addr = self.sender_addr.split(':')
                    self.sender_addr[1] = int(self.sender_addr[1])
                    self.sender_addr = tuple(self.sender_addr)

                case ["Via:", params]:
                    addr, branch = string_to_dict(params, "SIP/2.0/UDP {address};branch={branch}").values()
                    addr = addr.split(':')
                    addr[1] = int(addr[1])

                    self.via.append((tuple(addr), branch))

                case ["Max-Forwards:", params]:
                    self.max_forwards = int(params)

                case ["From:", params]:
                    if ";tag=" in params:
                        tmp = string_to_dict(params, "<sip:{sender}>;tag={tag}")
                        self.sender_addr = tmp["tag"]
                        self.sender_addr = self.sender_addr.split(':')
                        self.sender_addr[1] = int(self.sender_addr[1])
                        self.sender_addr = tuple(self.sender_addr)

                    else:
                        tmp = string_to_dict(params, "<sip:{sender}>")

                    self.aor = tmp["sender"]

                case ["To:", params]:
                    if ";tag=" in params:
                        tmp = string_to_dict(params, "<sip:{recipient}>;tag={tag}")
                        self.recipient_addr = tmp["tag"]
                        self.recipient_addr = self.recipient_addr.split(':')
                        self.recipient_addr[1] = int(self.recipient_addr[1])
                        self.recipient_addr = tuple(self.recipient_addr)

                    else:
                        tmp = string_to_dict(params, "<sip:{recipient}>")

                    self.recipient = tmp["recipient"]

                case ["Call-ID:", params]:
                    self.call_id = params

                case ["CSeq:", params]:
                    self.cseq = int(params.split()[0])

                case ["Content-Type:", params]:
                    pass

                case ["Content-Length:", params]:
                    pass

                case ["Expires:", params]:
                    self.expires = int(params)

                case ["Contact:", params]:
                    pass

                case _:
                    raise ValueError(f"Failed to parse header \"{header}\"!")

        self.content = body
        return self

    def __str__(self):
        register = f"REGISTER sip:{':'.join(map(str, self.sender_addr))} SIP/2.0\r\n"
        register += ''.join(f"Via: SIP/2.0/UDP {':'.join(map(str, address))};branch={branch}\r\n" for address, branch in self.via[::-1])
        register += f"Max-Forwards: {self.max_forwards}\r\n"
        register += f"From: <sip:{self.aor}>;tag={':'.join(map(str, self.sender_addr))}\r\n"
        register += f"Call-ID: {self.call_id}\r\n"
        register += f"To: <sip:{self.recipient}>\r\n"
        register += f"Expires: {self.expires}\r\n"
        register += f"CSeq: {self.cseq} REGISTER\r\n"
        register += f"Contact: sip:{self.aor}\r\n"
        register += f"Content-Length: 0\r\n\r\n"

        return register

    def response_headers(self):
        register = ''.join(f"Via: SIP/2.0/UDP {':'.join(map(str, address))};branch={branch}\r\n" for address, branch in self.via[::-1])
        register += f"From: <sip:{self.aor}>;tag={':'.join(map(str, self.sender_addr))}\r\n"
        register += f"Max-Forwards: {self.max_forwards}\r\n"
        register += f"Call-ID: {self.call_id}\r\n"
        register += f"To: <sip:{self.recipient}>\r\n"
        register += f"Expires: {self.expires}\r\n"
        register += f"CSeq: {self.cseq} REGISTER\r\n"
        register += f"Contact: sip:{self.aor}\r\n"
        register += f"Content-Length: 0\r\n\r\n"

        return register

    def __bytes__(self):
        return str(self).encode()
