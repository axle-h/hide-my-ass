from enum import Enum

__author__ = 'Alex Haslehurst'


class ProxyField(Enum):
    LastUpdate = 1
    IpAddress = 2
    Port = 3
    Country = 4
    Speed = 5
    ConnectionTime = 6
    Protocol = 7
    Anon = 8


class ProxyAnon(Enum):
    Low = 1,
    Medium = 2,
    High = 3,
    HighKa = 4


class ProxyProtocol(Enum):
    Http = 1,
    Https = 2,
    Socks = 3


class Proxy:
    def __init__(self, updated, ip, port, country, speed, time, protocol, anon):
        self.updated = updated
        self.ip = ip
        self.port = port
        self.country = country
        self.speed = speed
        self.connectionTime = time
        self.protocol = protocol
        self.anon = anon

    def __init__(self, fields):
        self.updated = fields[ProxyField.LastUpdate]
        self.ip = fields[ProxyField.IpAddress]
        self.port = fields[ProxyField.Port]
        self.country = fields[ProxyField.Country]
        self.speed = fields[ProxyField.Speed]
        self.connectionTime = fields[ProxyField.ConnectionTime]
        self.protocol = fields[ProxyField.Protocol]
        self.anon = fields[ProxyField.Anon]

    def __str__(self, *args, **kwargs):
        return "{0}, {1}:{2}, {3}, {4}, {5}, {6}, {7}".format(self.updated, self.ip, self.port, self.country,
                                                              self.speed, self.connectionTime, self.protocol,
                                                              self.anon)




