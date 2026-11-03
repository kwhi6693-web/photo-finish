"""Offline regressions for untrusted provider URLs and bounded acquisition."""
import io, socket, sys, tempfile, unittest, threading, time
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import workflow_session as w


def png():
    b=io.BytesIO();Image.new('RGB',(8,8)).save(b,format='PNG');return b.getvalue()

class DownloadHardeningTests(unittest.TestCase):
    def test_rejects_non_https_and_embedded_credentials(self):
        for url in ('http://example.com/x','https://' + 'u:p@' + 'example.com/x','https://example.com:8443/x'):
            with self.subTest(url=url), self.assertRaises(ValueError):w._validate_download_url(url)

    def test_rejects_private_and_mixed_dns_before_connect(self):
        for ips in (['127.0.0.1'],['169.254.169.254'],['10.0.0.1'],['::1'],['93.184.216.34','192.168.1.1']):
            answers=[(socket.AF_INET6 if ':' in ip else socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443,0,0) if ':' in ip else (ip,443)) for ip in ips]
            with self.subTest(ips=ips),patch.object(w.socket,'getaddrinfo',return_value=answers),patch.object(w.socket,'create_connection') as connect:
                with self.assertRaises(ValueError):w._download_connection('example.com',timeout=1)
                connect.assert_not_called()

    def test_connection_pins_resolved_public_address(self):
        answers=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
        with patch.object(w.socket,'getaddrinfo',return_value=answers):conn=w._download_connection('example.com',timeout=1)
        with patch.object(w.socket,'create_connection',return_value='synthetic-socket') as connect:
            self.assertEqual(conn._create_connection(('example.com',443),1),'synthetic-socket')
            self.assertEqual(connect.call_args.args[0],('93.184.216.34',443))
            self.assertEqual(conn.host,'example.com')

    def test_redirect_to_insecure_target_rejected_without_open(self):
        handler=w._DownloadRedirect();handler.parent=type('Parent',(),{'open':lambda *a,**k:self.fail('must not open')})()
        from urllib.request import Request
        response=io.BytesIO()
        with self.assertRaises(ValueError):handler.http_error_302(Request('https://example.com/a'),response,302,'Found',{'Location':'http://127.0.0.1/private'})
        self.assertTrue(response.closed)

    def test_redirect_revalidates_dns_and_closes_body(self):
        from urllib.request import Request
        handler=w._DownloadRedirect()
        class Parent:
            def open(self, request, timeout):
                return w._download_connection(request.host, timeout=timeout)
        handler.parent=Parent()
        request=Request('https://example.com/a');request.timeout=1
        response=io.BytesIO(b'untrusted redirect body')
        answers=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]
        with patch.object(w.socket,'getaddrinfo',return_value=answers),patch.object(w.socket,'create_connection') as connect:
            with self.assertRaises(ValueError):handler.http_error_302(request,response,302,'Found',{'Location':'https://other.example/b'})
            connect.assert_not_called()
        self.assertTrue(response.closed)

    def test_redirect_limit_closes_body_without_open(self):
        from urllib.request import Request
        handler=w._DownloadRedirect();handler.parent=type('Parent',(),{'open':lambda *a,**k:self.fail('must not open')})()
        request=Request('https://example.com/a');request._download_redirects=w.MAX_DOWNLOAD_REDIRECTS
        response=io.BytesIO()
        with self.assertRaisesRegex(ValueError,'redirect limit'):handler.http_error_302(request,response,302,'Found',{'Location':'/next'})
        self.assertTrue(response.closed)

    def test_stream_limit_cleans_up_and_never_publishes(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'result.png'
            with patch.object(w,'urlopen',return_value=io.BytesIO(png())),patch.object(w,'MAX_DOWNLOAD_BYTES',16):
                with self.assertRaisesRegex(ValueError,'size'):w.download_image('https://example.com/x',target)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_advertised_oversize_rejected_before_body(self):
        class Response(io.BytesIO):
            headers={'Content-Length':'999999999999'}
            def read(self,*a):raise AssertionError('body should not be read')
        with tempfile.TemporaryDirectory() as td,patch.object(w,'urlopen',return_value=Response()):
            with self.assertRaisesRegex(ValueError,'size'):w.download_image('https://example.com/x',Path(td)/'x.png')
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_total_deadline_cleans_up(self):
        with tempfile.TemporaryDirectory() as td,patch.object(w,'urlopen',return_value=io.BytesIO(png())),patch.object(w.time,'monotonic',side_effect=[0,0,2,2]):
            with self.assertRaises(TimeoutError):w.download_image('https://example.com/x',Path(td)/'x.png',timeout=1)
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_https_handler_uses_standard_context_without_legacy_attributes(self):
        from urllib.request import Request
        handler=w._DownloadHTTPS()
        response=io.BytesIO()
        with patch.object(handler, 'do_open', return_value=response):
            self.assertIs(handler.https_open(Request('https://example.com/x')), response)
        response.close()

    def _assert_drip_bounded(self, chunked):
        client, server=socket.socketpair()
        stop=threading.Event()
        class PlainTLS:
            def __init__(self, sock):self.sock=sock
            def __getattr__(self, name):return getattr(self.sock,name)
            def do_handshake(self):pass
            def setsockopt(self,*args):pass
        class Context:
            def wrap_socket(self, sock, **kwargs):return PlainTLS(sock)
        answers=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
        def drip():
            try:
                server.recv(8192)
                if chunked:server.sendall(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n0\r\n')
                else:server.sendall(b'HTTP/1.1 200 OK\r\n')
                for _ in range(60):
                    if stop.wait(0.02):break
                    server.sendall(b'X-Test: drip\r\n')
                server.sendall(b'\r\n')
            except OSError:pass
        worker=threading.Thread(target=drip,daemon=True);worker.start()
        started=None;conn=None;response=None
        try:
            with patch.object(w.socket,'getaddrinfo',return_value=answers),patch.object(w.socket,'create_connection',return_value=PlainTLS(client)):
                # Root-certificate initialization can exceed 150 ms on a busy
                # Windows runner. This fixture measures parser drips, so finish
                # connection setup before starting that deliberately tiny budget.
                conn=w._download_connection('example.com',timeout=5)
                conn._context=Context()
                started=time.monotonic()
                conn._download_deadline=started+0.15
                conn.request('GET','/')
                try:
                    response=conn.getresponse()
                    if chunked:response.read1(1024)
                except (OSError, w.http.client.HTTPException):pass
            self.assertLess(time.monotonic()-started,0.75,'slow headers/framing exceeded absolute budget')
        finally:
            stop.set()
            if response is not None:response.close()
            if conn is not None:
                conn.close()
                cancel=getattr(conn,'_cancel_download_deadline',None)
                if cancel:cancel()
            client.close();server.close();worker.join(timeout=1)

    def test_slow_headers_cannot_extend_absolute_deadline(self):
        self._assert_drip_bounded(False)

    def test_chunk_trailers_cannot_extend_absolute_deadline(self):
        self._assert_drip_bounded(True)

    def test_public_address_fallback_never_resolves_again(self):
        answers=[(socket.AF_INET,socket.SOCK_STREAM,6,'',(ip,443)) for ip in ('93.184.216.34','93.184.216.35')]
        with patch.object(w.socket,'getaddrinfo',return_value=answers) as lookup:
            conn=w._download_connection('example.com',timeout=1)
            with patch.object(w.socket,'create_connection',side_effect=[OSError('unavailable'),'socket']) as dial:
                self.assertEqual(conn._create_connection(('example.com',443),1),'socket')
                self.assertEqual([call.args[0][0] for call in dial.call_args_list],['93.184.216.34','93.184.216.35'])
            lookup.assert_called_once()
