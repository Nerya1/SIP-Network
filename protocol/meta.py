def __bytes__(self):
    return str(self).encode()


def __str__(self):
    ret = ""

    for field, expression in self._expressions.items():
        value = self.__getattribute__(field)

        match value:
            case list():
                for item in value:
                    ret += expression.format(item) + '\r\n'

            case _:
                ret += expression.format(value) + '\r\n'

    return ret + '\r\n' + self.body


def __init__(self, data):
    headers, _, body = data.partition('\r\n\r\n')

    for line in headers.split('\r\n'):
        for field, expression in self._expressions.items():
            start, _, end = expression.partition('{}')

            if line.startswith(start) and line.endswith(end):
                value = line[len(start):-len(end) or None]

                match self.__getattribute__(field):
                    case list():
                        self.__getattribute__(field).append(value)

                    case default:
                        self.__setattr__(field, type(default)(value))

    self.body = body


class Packet(type):
    def __new__(cls, name, bases, dct):
        modified = {
            '_expressions': {},
            '__bytes__': __bytes__,
            '__str__': __str__,
            '__init__': __init__
        }

        for key, value in dct.items():
            if key.startswith('__'):
                modified["key"] = value

            else:
                modified['_expressions'][key] = value[0]
                modified[key] = value[1]()

        return super().__new__(cls, name, bases, modified)
