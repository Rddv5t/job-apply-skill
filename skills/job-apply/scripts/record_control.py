"""Serve a loopback-only UI that the tracker content script and huashu can operate."""
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>秋招助手记录同步</title><style>
body{font:17px system-ui;max-width:900px;margin:60px auto;padding:24px;color:#17223b}
button,input{font:inherit;padding:12px;margin:12px 12px 12px 0}p{line-height:1.7}
</style><body><p>本页只在本机提供投递记录控件，不向外网发送数据。</p>
<p>若没有出现“秋招助手 · 投递记录控制”，请重新加载升级后的秋招助手扩展，再刷新此页。</p></body></html>'''.encode('utf-8')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get('Host') != '127.0.0.1:18765' or self.path != '/records':
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(PAGE)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(PAGE)

    def log_message(self, *_):
        pass


if __name__ == '__main__':
    print('Local record controls: http://127.0.0.1:18765/records', flush=True)
    HTTPServer(('127.0.0.1', 18765), Handler).serve_forever()
