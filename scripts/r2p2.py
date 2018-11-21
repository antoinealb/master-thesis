from scapy.all import *

class R2P2(Packet):
    name = "R2P2Header"
    fields_desc = [ByteField("magic", 0), ByteField("header_size", 8),
            BitEnumField('type', 0, 4, {0: 'REQUEST', 1: 'RESPONSE', 3: 'ACK'}),
            BitField('policy', 0, 4),
            FlagsField("state", 0, 2, ['f', 'l']),
            BitField('reserved', 0, 6),
            ShortField("request_id", 0),
            ShortField("packet_id", 0)]

class Raft(Packet):
    name = "Raft"
    fields_desc = [LEIntField("type", 0), LEIntField("term", 0), LEIntField("from", 0)]


bind_layers(UDP, R2P2, dport=9000)
bind_layers(UDP, R2P2, sport=9000)
bind_layers(UDP, R2P2, dport=8000)
bind_layers(UDP, R2P2, sport=8000)

bind_layers(R2P2, Raft, type=4)
