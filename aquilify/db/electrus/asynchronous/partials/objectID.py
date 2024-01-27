import os
import time
import hashlib
import random

from typing import Optional

class ObjectId:
    @staticmethod
    def generate() -> str:
        timestamp: int = int(time.time())
        machine_id: str = ObjectId._generate_machine_id()
        process_id: int = os.getpid() & 0xFFFF
        counter: int = random.randint(0, 0xFFFFFF)
        return f'{timestamp:08x}{machine_id}{process_id:04x}{counter:06x}'.zfill(24)

    @staticmethod
    def _generate_machine_id() -> str:
        try:
            mac_address: Optional[bytes] = ObjectId._get_mac_address()
            if mac_address:
                machine_id: str = hashlib.md5(mac_address).hexdigest()[:6]
                return machine_id
            return '000000'
        except Exception:
            return '000000'

    @staticmethod
    def _get_mac_address() -> Optional[bytes]:
        try:
            if hasattr(os, 'getrandom') and os.name != 'nt':
                return os.getrandom(6) if os.name != 'nt' else None
            elif hasattr(os, 'urandom'):
                return os.urandom(6)
        except Exception:
            pass
        return None
