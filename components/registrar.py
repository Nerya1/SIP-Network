from protocol import sip
from components.base import AS, database

from copy import deepcopy


class Registrar(AS):
    def __init__(self, addr, timeout):
        super().__init__(addr)

        self.time_limit = timeout

    @database('./data/aor.json')
    def process_request(self, request, data):
        invite = sip.Register()
        invite = invite.from_string(request)

        self.respond("100 Trying", deepcopy(invite))

        if f"{invite.sender_addr[0]}:{invite.sender_addr[1]}" not in data[invite.aor].keys() and data[invite.aor]:
            self.respond("501 Not Implemented", deepcopy(invite))
            return data, None

        data.setdefault(invite.aor, {})[f"{invite.sender_addr[0]}:{invite.sender_addr[1]}"] = self.time_limit
        self.respond("200 OK", deepcopy(invite))

        return data, None

    @database('./data/aor.json')
    def timeout(self, dt, data):
        removed = set()

        for aor, addresses in data.items():
            for key in addresses.keys():
                addresses[key] -= dt

                if addresses[key] <= 0:
                    removed.add((aor, key))

        for aor, key in removed:
            data[aor].pop(key)

        return data, removed
