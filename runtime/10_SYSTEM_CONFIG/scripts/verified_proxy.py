"""Explicit loopback proxy transport with HTTPS DNS and numeric CONNECT targets.

Never discovers ambient proxies. The operator must opt in to a trusted local
gateway; signed paths/queries are sent only to their intended HTTPS origin.
"""
import http.client
import ipaddress
import json
import re
import socket
import ssl
import threading
import time
from urllib.parse import urlsplit, urlencode

MAX_DNS_BYTES = 65536
RESOLVER_HOST = 'cloudflare-dns.com'
RESOLVER_ADDRESS = '1.1.1.1'


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('Download total deadline exceeded')
    return remaining


def _public(address):
    ip = ipaddress.ip_address(address)
    mapped = getattr(ip, 'ipv4_mapped', None)
    translated = (isinstance(ip, ipaddress.IPv6Address) and
                  (ip in ipaddress.ip_network('64:ff9b::/96') or
                   ip in ipaddress.ip_network('64:ff9b:1::/48') or ip.sixtofour or ip.teredo))
    if not ip.is_global or (mapped is not None and not mapped.is_global) or translated:
        raise ValueError('Download target must resolve only to public addresses')
    return str(ip)


def _domain(name):
    try:
        name = name.rstrip('.').encode('idna').decode('ascii').lower()
    except (AttributeError, UnicodeError):
        raise ValueError('Invalid download DNS name') from None
    labels = name.split('.')
    if (len(name) > 253 or len(labels) < 2 or
            any(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) is None for label in labels) or
            labels[-1] in {'localhost', 'local', 'internal', 'test', 'invalid', 'example', 'onion', 'arpa'}):
        raise ValueError('Download requires a public DNS name')
    return name


class _ProxyTLSConnection(http.client.HTTPSConnection):
    def __init__(self, host, address, proxy, deadline, context=None):
        super().__init__(host, port=443, timeout=_remaining(deadline),
                         context=context or ssl.create_default_context())
        self._proxy_endpoint = proxy
        self._download_deadline = deadline
        address = _public(address)
        authority = ('[' + address + ']' if ':' in address else address) + ':443'
        self.set_tunnel(address, 443, headers={'Host': authority})

    def connect(self):
        self.sock = socket.create_connection(self._proxy_endpoint, _remaining(self._download_deadline))
        # Keep the socket object alive after HTTPConnection passes it to the
        # response. Retarget after SSL takes ownership; never retain a raw fd.
        holder = {'socket': self.sock}
        def expire():
            try: holder['socket'].shutdown(socket.SHUT_RDWR)
            except OSError: pass
        try:
            self._download_timer = threading.Timer(_remaining(self._download_deadline), expire)
            self._download_timer.daemon = True
            self._download_timer.start()
            self._tunnel()  # Numeric, already-public IP; no proxy-side name lookup.
            self.sock = self._context.wrap_socket(self.sock, server_hostname=self.host,
                                                  do_handshake_on_connect=False)
            holder['socket'] = self.sock
            self.sock.settimeout(_remaining(self._download_deadline))
            self.sock.do_handshake()
        except BaseException:
            self._cancel_download_deadline()
            self.close()
            raise

    def _cancel_download_deadline(self):
        timer = getattr(self, '_download_timer', None)
        if timer is not None:
            timer.cancel()


class VerifiedProxy:
    def __init__(self, url):
        try:
            parsed = urlsplit(url)
            address = ipaddress.ip_address(parsed.hostname)
            port = parsed.port
            if (parsed.scheme != 'http' or not address.is_loopback or port is None or
                    not 1 <= port <= 65535 or parsed.username is not None or
                    parsed.password is not None or parsed.path not in ('', '/') or
                    parsed.query or parsed.fragment or any(ord(c) < 33 or ord(c) == 127 for c in url)):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError('Verified proxy requires an explicit HTTP loopback IP and port without credentials') from None
        self.endpoint = (str(address), port)

    def _query(self, name, record_type, deadline):
        # Bootstrap the HTTPS resolver by a fixed public address, also through
        # numeric CONNECT. The original resolver hostname verifies its TLS cert.
        connection = _ProxyTLSConnection(RESOLVER_HOST, RESOLVER_ADDRESS, self.endpoint, deadline)
        response = None
        try:
            query = urlencode({'name': name, 'type': 'A' if record_type == 1 else 'AAAA'})
            connection.request('GET', '/dns-query?' + query,
                               headers={'Host': RESOLVER_HOST, 'Accept': 'application/dns-json',
                                        'Connection': 'close'})
            response = connection.getresponse()
            if response.status != 200:
                raise ValueError('Verified DNS resolver rejected request')
            length = response.headers.get('Content-Length')
            if length is not None and (not length.isdigit() or int(length) > MAX_DNS_BYTES):
                raise ValueError('Verified DNS response exceeds limit')
            data = response.read(MAX_DNS_BYTES + 1)
            _remaining(deadline)
            if len(data) > MAX_DNS_BYTES:
                raise ValueError('Verified DNS response exceeds limit')
            try:
                payload = json.loads(data)
            except (ValueError, UnicodeError):
                raise ValueError('Invalid verified DNS response') from None
            return self._answers(payload, name, record_type)
        finally:
            if response is not None: response.close()
            connection._cancel_download_deadline()
            connection.close()

    @staticmethod
    def _answers(payload, name, record_type):
        if (not isinstance(payload, dict) or type(payload.get('Status')) is not int or
                payload['Status'] != 0 or payload.get('TC', False) is not False):
            raise ValueError('Verified DNS query failed or was truncated')
        questions = payload.get('Question')
        if (not isinstance(questions, list) or len(questions) != 1 or
                not isinstance(questions[0], dict) or
                _domain(questions[0].get('name')) != name or
                type(questions[0].get('type')) is not int or questions[0]['type'] != record_type):
            raise ValueError('Verified DNS question differs')
        records = payload.get('Answer', [])
        if not isinstance(records, list) or len(records) > 64:
            raise ValueError('Invalid verified DNS answer set')
        links = {}
        for record in records:
            if not isinstance(record, dict) or type(record.get('type')) is not int:
                raise ValueError('Invalid verified DNS record')
            if record['type'] == 5:
                owner, target = _domain(record.get('name')), _domain(record.get('data'))
                if owner in links and links[owner] != target:
                    raise ValueError('Conflicting verified DNS aliases')
                links[owner] = target
        chain = {name}
        owner = name
        while owner in links:
            owner = links[owner]
            if owner in chain or len(chain) >= 16:
                raise ValueError('Invalid verified DNS alias chain')
            chain.add(owner)
        addresses = []
        for record in records:
            if record['type'] in (1, 28):
                address = _public(record.get('data'))
                if (_domain(record.get('name')) not in chain or
                        ipaddress.ip_address(address).version != (4 if record['type'] == 1 else 6)):
                    raise ValueError('Verified DNS address does not match query')
                addresses.append(address)
        return addresses

    def connection(self, host, timeout=30, context=None, deadline=None):
        deadline = time.monotonic() + timeout if deadline is None else deadline
        parsed = urlsplit('https://' + host)
        if (not parsed.hostname or parsed.username is not None or parsed.password is not None or
                parsed.port not in (None, 443) or parsed.path or parsed.query or parsed.fragment):
            raise ValueError('Invalid verified download host')
        try:
            address = ipaddress.ip_address(parsed.hostname)
        except ValueError:
            name = _domain(parsed.hostname)
            # Validate both address families before opening any target tunnel.
            addresses = self._query(name, 1, deadline) + self._query(name, 28, deadline)
        else:
            name, addresses = parsed.hostname, [_public(address)]
        if not addresses:
            raise ValueError('Download host has no public address')
        addresses = [_public(address) for address in addresses]
        return _ProxyTLSConnection(name, addresses[0], self.endpoint, deadline, context)
