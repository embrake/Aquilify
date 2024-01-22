import random
import time
import hashlib
import string
from typing import List, Optional

class EIDS:
    @staticmethod
    def eid1(node_id: int) -> str:
        timestamp: int = int(time.time() * 1e9)
        clock_seq: int = random.getrandbits(14)
        eid: int = (timestamp << 64) | (clock_seq << 50) | 0x1000000000000000
        eid |= node_id
        return EIDS.format_eid(eid)
    
    @staticmethod
    def eid2(node_id: int, domain_id: int) -> str:
        timestamp: int = int(time.time())
        clock_seq: int = random.getrandbits(14)
        eid: int = (timestamp << 32) | (clock_seq << 16) | 0x2000
        eid |= (node_id << 48) | domain_id
        return EIDS.format_eid(eid)
    
    @staticmethod
    def eid3(name: str) -> str:
        namespace_eid: str = EIDS.eid1(node_id=0x123456789abc)
        hashed_name: str = hashlib.md5((namespace_eid + name).encode('utf-8')).hexdigest()
        eid: str = EIDS.format_advance(hashed_name, version=3)
        return eid
    
    @staticmethod
    def eid4() -> str:
        eid: int = random.getrandbits(128)
        return EIDS.format_eid(eid)
    
    @staticmethod
    def eid5(namespace: str, name: str) -> str:
        namespace_eid: str = EIDS.eid1(node_id=0x123456789abc)
        hashed_name: str = hashlib.sha1((namespace_eid + name).encode('utf-8')).hexdigest()
        namespace_hex: str = namespace.replace('-', '')
        eid: str = hashed_name[:16] + '-' + hashed_name[16:20] + '-5' + hashed_name[21:24] + '-' + namespace_hex[:4] + '-' + namespace_hex[4:16]
        return eid
    
    @staticmethod
    def default_end() -> int:
        timestamp: int = int(time.time())
        random_part: int = random.getrandbits(64)
        eid: int = (timestamp << 64) | random_part
        return eid
    
    @staticmethod
    def format_advance(eid_str: str, version: int) -> str:
        parts: List[str] = [eid_str[:8], eid_str[8:12], str(version) + eid_str[13:16], eid_str[16:20], eid_str[20:]]
        return '-'.join(parts)
    
    @staticmethod
    def format_eid(eid: int) -> str:
        eid_str: str = f"{eid:032x}"
        formatted_eid: str = f"{eid_str[:8]}-{eid_str[8:12]}-{eid_str[12:16]}-{eid_str[16:20]}-{eid_str[20:]}"
        return formatted_eid
    
    @staticmethod
    def random(length: int = 10) -> str:
        if length < 2:
            raise ValueError("Length must be at least 2.")
        remaining_length: int = length - 2
        random_digits: str = ''.join(random.choice(string.digits) for _ in range(remaining_length))
        unique_id: str = random_digits
        return unique_id

class Eid:
    def __init__(self, node: Optional[int] = None, clock_seq: Optional[int] = None) -> None:
        self.node: int = node if node is not None else random.getrandbits(48)
        self.clock_seq: int = clock_seq if clock_seq is not None else random.getrandbits(14)
        self.variant_bits: int = 0b1000

    def chip1(self) -> str:
        timestamp: int = int(time.time() * 1e7) + 0x01b21dd213814000
        timestamp_hex: str = format(timestamp, '032x')
        clock_seq_hex: str = format(self.clock_seq, '04x')
        node_hex: str = format(self.node, '012x')
        eid: str = f"{timestamp_hex[:8]}-{timestamp_hex[8:12]}-{timestamp_hex[12:16]}-{clock_seq_hex[0]}{timestamp_hex[16:]}-{node_hex}"
        return eid

    def chip3(self, name: str, namespace_eid: str) -> str:
        hash_obj: hashlib._hashlib.HASH = hashlib.sha1(namespace_eid.encode('utf-8') + name.encode('utf-8'))
        hash_bytes: bytes = hash_obj.digest()
        hash_int: int = int.from_bytes(hash_bytes, 'big')
        eid: str = f"{hash_int:032x}"
        return eid

    def chip4(self) -> str:
        random_bits_hex: str = format(random.getrandbits(128), '032x')
        eid: str = f"{random_bits_hex[:8]}-{random_bits_hex[8:12]}-4{random_bits_hex[13:16]}-{self.variant_bits}{random_bits_hex[16:20]}-{random_bits_hex[20:]}"
        return eid

    def chip2(self, domain: Optional[str] = None) -> str:
        if domain is None:
            raise ValueError("Domain is required for version 2 UUID.")
        timestamp: int = int(time.time() * 1e7) + 0x01b21dd213814000
        timestamp_hex: str = format(timestamp, '032x')
        clock_seq_hex: str = format(self.clock_seq, '04x')
        node_hex: str = format(self.node, '012x')
        eid: str = f"{domain[:8]}-{timestamp_hex[8:12]}-{timestamp_hex[12:16]}-{clock_seq_hex[0]}{timestamp_hex[16:]}-{node_hex}"
        return eid

eid = EIDS()
