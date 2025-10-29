import struct

def serialize_int(value: int) -> bytes:
    return struct.pack(">I", value)

def deserialize_int(b: bytes) -> int:
    return struct.unpack(">I", b)[0]
