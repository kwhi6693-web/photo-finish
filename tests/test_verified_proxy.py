"""Opt-in pinned proxy acquisition; no external network in these regressions."""
import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request
from PIL import Image
import workflow_session as w
import verified_proxy as v


class PlainTLS:
    """Offline TLS boundary double; real TLS is verified by the scoped live trial."""
    def __init__(self, sock): self.sock = sock
    def __getattr__(self, name): return getattr(self.sock, name)
    def do_handshake(self): pass


class Context:
    def __init__(self): self.server_names = []
    def wrap_socket(self, sock, *, server_hostname, do_handshake_on_connect):
        assert do_handshake_on_connect is False
        self.server_names.append(server_hostname)
        return PlainTLS(sock)


def payload(addresses, *, name='example.com', record_type=1):
    return {'Status': 0, 'TC': False, 'Question': [{'name': name, 'type': record_type}],
            'Answer': [{'name': name, 'type': 28 if ':' in ip else 1, 'data': ip} for ip in addresses]}


def png():
    b=io.BytesIO(); Image.new('RGB',(8,8)).save(b,format='PNG'); return b.getvalue()


class SocketProxy:
    def __init__(self, response, *, drip=False):
        self.client,self.server=socket.socketpair()
        self.response=response; self.drip=drip; self.requests=[]; self.errors=[]
        self.stop=threading.Event()
        self.worker=threading.Thread(target=self.run,daemon=True)
        self.worker.start()
    def headers(self):
        data=b''
        while not data.endswith(b'\r\n\r\n'):
            block=self.server.recv(1)
            if not block:raise OSError('client closed')
            data+=block
        self.requests.append(data)
    def run(self):
        try:
            self.headers()
            if self.drip:
                self.server.sendall(b'HTTP/1.1 200 Connection established\r\n')
                for _ in range(60):
                    if self.stop.wait(0.02):return
                    self.server.sendall(b'X-Proxy: slow\r\n')
                self.server.sendall(b'\r\n')
            else:
                self.server.sendall(b'HTTP/1.1 200 Connection established\r\n\r\n')
                self.headers();self.server.sendall(self.response)
        except OSError: pass
    def close(self):
        self.stop.set()
        for s in (self.client,self.server):
            try:s.shutdown(socket.SHUT_RDWR)
            except OSError:pass
            s.close()
        self.worker.join(timeout=1)


class ProxyOptInTests(unittest.TestCase):
    def test_explicit_remote_proxy_is_rejected_before_transport(self):
        with patch.dict(os.environ, {'PHOTO_FINISH_DOWNLOAD_PROXY': 'http://192.168.1.5:8080'}):
            with patch.object(w, 'build_opener') as opener:
                with self.assertRaises(ValueError):
                    w.urlopen(Request('https://example.com/image.png'), timeout=1)
                opener.assert_not_called()

    def test_ambient_proxy_does_not_enable_new_transport(self):
        with patch.dict(os.environ, {'HTTPS_PROXY':'http://127.0.0.1:1234'}):
            os.environ.pop('PHOTO_FINISH_DOWNLOAD_PROXY',None)
            with patch.object(w,'build_opener') as build:
                w.urlopen(Request('https://example.com/x'),timeout=1)
                handler=next(x for x in build.call_args.args if isinstance(x,w._DownloadHTTPS))
                self.assertIsNone(getattr(handler,'verified_proxy',None))

    def test_only_explicit_numeric_loopback_gateway_is_accepted(self):
        invalid=['http://localhost:8080','https://127.0.0.1:8080','http://127.0.0.1',
                 'http://127.0.0.1:8080/path','http://127.0.0.1:8080?x=1',
                 'http://127.0.0.1:8080#fragment']
        userinfo=':'.join(('name','secret'))+'@'
        invalid.append('http://'+userinfo+'127.0.0.1:8080')
        for url in invalid:
            with self.subTest(url=url),self.assertRaises(ValueError):v.VerifiedProxy(url)
        self.assertEqual(v.VerifiedProxy('http://[::1]:8080').endpoint,('::1',8080))

    def test_private_ipv6_answer_blocks_all_public_a_answers(self):
        transport=v.VerifiedProxy('http://127.0.0.1:8080')
        def query(name,kind,deadline):
            return v.VerifiedProxy._answers(payload(['93.184.216.34'] if kind==1 else ['::1'],record_type=kind),name,kind)
        with patch.object(transport,'_query',side_effect=query),patch.object(v.socket,'create_connection') as dial:
            with self.assertRaisesRegex(ValueError,'public'):transport.connection('example.com',timeout=1)
            dial.assert_not_called()

    def test_dns_rejects_mismatched_questions_aliases_and_addresses(self):
        bad=[]
        p=payload(['93.184.216.34']);p['Question'][0]['name']='other.example.com';bad.append(p)
        p=payload(['93.184.216.34']);p['TC']=True;bad.append(p)
        p=payload(['93.184.216.34']);p['Status']=3;bad.append(p)
        p=payload(['93.184.216.34']);p['Answer'][0]['name']='other.example.com';bad.append(p)
        p=payload(['93.184.216.34']);p['Answer']+=[{'name':'example.com','type':5,'data':'example.com'}];bad.append(p)
        p=payload(['93.184.216.34']);p['Answer'][0]['type']=28;bad.append(p)
        for p in bad:
            with self.subTest(payload=p),self.assertRaises(ValueError):v.VerifiedProxy._answers(p,'example.com',1)

    def test_valid_cname_chain_retains_only_public_bound_addresses(self):
        p={'Status':0,'Question':[{'name':'example.com.','type':1}],
           'Answer':[{'name':'example.com.','type':5,'data':'cdn.example.com.'},
                     {'name':'cdn.example.com.','type':1,'data':'93.184.216.34'}]}
        self.assertEqual(v.VerifiedProxy._answers(p,'example.com',1),['93.184.216.34'])

    def test_numeric_connect_keeps_origin_host_and_full_response_bytes(self):
        body=png(); proxy=SocketProxy(b'HTTP/1.1 200 OK\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body)
        self.addCleanup(proxy.close);context=Context()
        conn=v._ProxyTLSConnection('example.com','93.184.216.34',('127.0.0.1',8080),time.monotonic()+5,context)
        try:
            with patch.object(v.socket,'create_connection',return_value=proxy.client):
                conn.request('GET','/image?signature=fixture',headers={'Host':'example.com','Connection':'close'})
                with conn.getresponse() as response:self.assertEqual(response.read(),body)
            self.assertTrue(proxy.requests[0].startswith(b'CONNECT 93.184.216.34:443 '))
            self.assertNotIn(b'example.com',proxy.requests[0]);self.assertNotIn(b'signature',proxy.requests[0])
            self.assertIn(b'Host: example.com',proxy.requests[1])
            self.assertEqual(context.server_names,['example.com'])
        finally:conn._cancel_download_deadline();conn.close()

    def test_slow_proxy_connect_headers_cannot_extend_deadline(self):
        proxy=SocketProxy(b'',drip=True);self.addCleanup(proxy.close)
        conn=v._ProxyTLSConnection('example.com','93.184.216.34',('127.0.0.1',8080),time.monotonic()+5,Context())
        started=time.monotonic();conn._download_deadline=started+0.15
        try:
            with patch.object(v.socket,'create_connection',return_value=proxy.client):
                with self.assertRaises((OSError, v.http.client.HTTPException)):conn.connect()
            self.assertLess(time.monotonic()-started,0.75)
            self.assertIsNone(conn.sock)
        finally:conn._cancel_download_deadline();conn.close()

    def test_ipv6_tunnel_header_is_bracketed(self):
        conn=v._ProxyTLSConnection('example.com','2606:4700::1111',('127.0.0.1',8080),time.monotonic()+5,Context())
        self.assertEqual(conn._tunnel_headers['Host'],'[2606:4700::1111]:443')

    def test_dns_redirect_is_not_followed_and_socket_is_closed(self):
        proxy=SocketProxy(b'HTTP/1.1 302 Found\r\nLocation: https://127.0.0.1/x\r\nContent-Length: 0\r\n\r\n')
        self.addCleanup(proxy.close);transport=v.VerifiedProxy('http://127.0.0.1:8080')
        with patch.object(v.socket,'create_connection',return_value=proxy.client),patch.object(v.ssl,'create_default_context',return_value=Context()):
            with self.assertRaisesRegex(ValueError,'resolver rejected'):transport._query('example.com',1,time.monotonic()+5)
        self.assertEqual(len(proxy.requests),2)
        self.assertTrue(proxy.requests[0].startswith(b'CONNECT 1.1.1.1:443 '))

    def test_dns_body_limit_prevents_reading_unbounded_json(self):
        proxy=SocketProxy(b'HTTP/1.1 200 OK\r\nContent-Length: 65537\r\n\r\n')
        self.addCleanup(proxy.close);transport=v.VerifiedProxy('http://127.0.0.1:8080')
        with patch.object(v.socket,'create_connection',return_value=proxy.client),patch.object(v.ssl,'create_default_context',return_value=Context()):
            with self.assertRaisesRegex(ValueError,'exceeds limit'):transport._query('example.com',1,time.monotonic()+5)

    def test_full_acquisition_with_proxy_preserves_image_hash(self):
        import hashlib
        body=png();proxy=SocketProxy(b'HTTP/1.1 200 OK\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body)
        self.addCleanup(proxy.close)
        with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'PHOTO_FINISH_DOWNLOAD_PROXY':'http://127.0.0.1:8080'}),patch.object(v.socket,'create_connection',return_value=proxy.client),patch.object(v.ssl,'create_default_context',return_value=Context()),patch.object(v.VerifiedProxy,'_query',side_effect=lambda n,t,d:['93.184.216.34'] if t==1 else []):
            target=Path(td)/'result.png';result=w.download_image('https://example.com/image',target,expected_sha256=hashlib.sha256(body).hexdigest())
            self.assertEqual(target.read_bytes(),body);self.assertEqual(result['format'],'PNG')
            self.assertEqual(len(list(Path(td).iterdir())),1)

    def test_private_redirect_never_opens_a_second_tunnel(self):
        proxy=SocketProxy(b'HTTP/1.1 302 Found\r\nLocation: https://127.0.0.1/private\r\nContent-Length: 0\r\n\r\n')
        self.addCleanup(proxy.close)
        with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{'PHOTO_FINISH_DOWNLOAD_PROXY':'http://127.0.0.1:8080'}),patch.object(v.socket,'create_connection',return_value=proxy.client) as dial,patch.object(v.ssl,'create_default_context',return_value=Context()),patch.object(v.VerifiedProxy,'_query',side_effect=lambda n,t,d:['93.184.216.34'] if t==1 else []):
            with self.assertRaisesRegex(ValueError,'public'):w.download_image('https://example.com/image',Path(td)/'result.png')
            self.assertEqual(dial.call_count,1);self.assertEqual(list(Path(td).iterdir()),[])
