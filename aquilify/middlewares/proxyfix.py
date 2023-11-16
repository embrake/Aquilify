from typing import List, Tuple

from ..wrappers import Request, Response

class ProxyFix:
    def __init__(
        self,
        app,
        num_proxies: int = 1,
        trusted_proxies: List[str] = None,
        headers_to_check: List[str] = None,
        trusted_hostnames: List[str] = None,
    ):
        self.app = app
        self.num_proxies = num_proxies
        self.trusted_proxies = set(trusted_proxies) if trusted_proxies else set()
        self.headers_to_check = headers_to_check or ['x-forwarded-for', 'x-real-ip', 'forwarded']
        self.trusted_hostnames = set(trusted_hostnames) if trusted_hostnames else set()

    async def __call__(
        self, request: Request, response: Response
    ) -> Response:
        remote_address, forwarded_proto, hostname = self.extract_client_info(request)

        if self.is_trusted_proxy(remote_address):
            request.client = remote_address

        if forwarded_proto:
            request.scope['scheme'] = forwarded_proto

        return response

    def extract_client_info(self, request: Request) -> Tuple[str, str, str]:
        remote_address = request.client
        forwarded_proto = None
        hostname = request.url.hostname if request.url else ''

        for header_name in self.headers_to_check:
            if header_name in request.headers:
                ips = [ip.strip() for ip in request.headers[header_name].split(',')]
                remote_address = self.extract_real_client_ip(ips)
                if header_name.lower() == 'x-forwarded-proto':
                    forwarded_proto = self.extract_forwarded_proto(request.headers[header_name])
                break

        return remote_address, forwarded_proto, hostname

    def extract_real_client_ip(self, ips: List[str]) -> str:
        client_ip = ips[-self.num_proxies]
        if ',' in client_ip:
            client_ip = client_ip.split(',')[-self.num_proxies].strip()

        if client_ip.startswith('[') and client_ip.endswith(']'):
            client_ip = client_ip[1:-1]

        return client_ip.rsplit(':', 1)[0].strip()

    def extract_forwarded_proto(self, header_value: str) -> str:
        proto_values = header_value.split(',')
        for proto in proto_values:
            proto = proto.strip().lower()
            if proto in ('https', 'http'):
                return proto

        return ''

    def is_trusted_proxy(self, remote_address: str) -> bool:
        return remote_address in self.trusted_proxies

    def remove_header_to_check(self, header_name: str) -> None:
        if header_name in self.headers_to_check:
            self.headers_to_check.remove(header_name)
