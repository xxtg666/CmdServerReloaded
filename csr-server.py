server_port = [8631, 8632, 34568]
enable_password = True
password = "123456"

# TO-DO:log系统
import socket
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
import base64
from urllib.parse import unquote
import sys, os
import traceback
import random
import time
import urllib

def base64encode(string):
    return base64.b64encode(string.encode()).decode()

def base64decode(string):
    return base64.b64decode(string.encode()).decode()

def generateMessageId(length=6):
    return "".join(random.choices("1234567890qwertyuiopasdfghjklzxcvbnm", k=length))
def restart_program():
  python = sys.executable
  os.execl(python, python, *sys.argv)

def log(m,level="INFO"):
    if m.startswith("Traceback"):
        level="ERROR"
    l = time.strftime("[%H:%M:%S]")+f" [{level}] {m}"
    print(l)
    with open("logs/latest.log","a") as f:
        f.write(l+"\n")

fallbacks = {}
s = socket.socket()
s.bind(("0.0.0.0", server_port[0]))
s.listen()
n = 0
connects = []
trusted = []
no_fallback_time = 0
server_files = {}
def init_log():
    try:
        os.mkdir("logs")
    except:
        pass
    if os.path.exists("logs/latest.log"):
        os.rename("logs/latest.log",f"logs/latest.{generateMessageId(10)}.log")
    with open("logs/latest.log","w") as f:
        f.write("")
def file(name,mod={}):
    global server_files
    DEV_MODE = True # 开发者测试WebUI用
    if DEV_MODE:
        with open("csr-server"+os.sep+name, "r", encoding="utf-8") as f:
            re = f.read()
    else:
        try:
            re = server_files[name]
        except KeyError:
            with open("csr-server"+os.sep+name, "r", encoding="utf-8") as f:
                server_files[name] = f.read()
        re = server_files[name]
    for k in list(mod.keys()):
        re = re.replace(f"%{k}%",str(mod[k]))
    return re
def no_fallback_time_count():
    global no_fallback_time
    global fallbacks
    log("no_fallback_time_count started")
    while True:
        no_fallback_time += 1
        if no_fallback_time >= 10:
            fallbacks = {}
        time.sleep(1)


def send_message(x, type, message):
    id = generateMessageId()
    connects[x]["connection"].send(
        f"{type}|{base64encode(message)}|{id}".encode("UTF-8")
    )
    return id


def start_input_thread():
    global password
    global trusted
    global enable_password
    global connects
    log("input_thread started")
    while True:
        l = input("> ")
        i = l.split(" ")
        try:
            if i[0] == "help":
                print(file("help.txt"))
            elif i[0] == "exit":
                os._exit(0)
            elif i[0] == "restart":
                restart_program()
            elif i[0] == "send":
                send_message(int(i[1]), i[2], i[3])
                print("=> message sent to " + i[1])
            elif i[0] == "trust":
                trusted.append(i[1])
                print("=> " + i[1] + " trusted")
            elif i[0] == "distrust":
                trusted.remove(i[1])
                print("=> " + i[1] + " removed from trusted")
            elif i[0] == "trusted":
                print("=> trusted list: " + str(trusted))
            elif i[0] == "password":
                print("=> password is " + password)
            elif i[0] == "changePassword":
                password = i[1]
                print("=> password change to " + password)
            elif i[0] == "enablePassword":
                enable_password = bool(i[1])
                print("=> enable password set to " + str(enable_password))
            elif i[0] == "list":
                print("=> client list (id|address|username|status)")
                for x in range(len(connects)):
                    print(
                        f"{str(x)} | {connects[x]['address']} | {connects[x]['username']} | {connects[x]['status']}"
                    )
            elif i[0] == "disconnect":
                connects[int(i[1])]["status"] = False
                print("=> client " + i[1] + " disconnected")
            else:
                print("=> unknown command. type help for help.")
        except:
            print("=> command error:\n" + traceback.format_exc())


def start_tcp_server():
    global n
    global connects
    global s
    log("tcp_server started")
    while True:
        c, addr = s.accept()
        connects.append(
            {"connection": c, "address": addr, "username": "", "status": True}
        )
        messageid = send_message(n, "username", "username")
        for _ in range(10):
            time.sleep(0.25)
            try:
                username = f"""{base64decode(fallbacks[messageid])}""".replace("\n", "")
                connects[n]["username"] = username
                break
            except KeyError:
                log("Waiting for fallback [" + messageid + "]")
            except:
                log(traceback.format_exc())
        log(f"{n}{addr}Connected")
        n += 1


class Request(BaseHTTPRequestHandler):
    timeout = 5
    server_version = "Apache"

    def do_GET(self):
        global trusted
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        req = str(self.raw_requestline, "iso-8859-1")
        ireq = str(req.replace("GET ", "").replace(" HTTP/1.1", "").replace("\n", ""))
        prefix = file("prefix.html",{
            "ireq":ireq
        })
        buf = ""
        log(ireq)
        log(self.address_string())
        if ireq.startswith("/static"):
            buf = file(ireq.split("/")[-1].replace("\r", ""))
        elif self.address_string() in trusted or not enable_password:
            if ireq.startswith("/log"):
                with open("logs/latest.log","r",encoding="utf-8") as f:
                    buf = f.read().replace("\n\n","\n").replace("\n","<br>")
            elif ireq.startswith("/restart"):
                restart_program()
            elif ireq[0:6] == "/index":
                v = ""
                for i in range(len(connects)):
                    v += file("index-tr.html",{
                        "id":i,
                        "address":connects[i]["address"],
                        "username":connects[i]["username"],
                        "status":connects[i]["status"],
                    }).replace("\n", "")
                buf = prefix+file("index-table.html",{
                    "v":v
                })
            elif ireq[0:11] == "/send-page/":  # /send-page/0
                id = ireq.replace("/send-page/", "")
                if connects[int(id)]["status"]:
                    buf = prefix + file("send-page.html",{
                        "id":id.replace("\n",""),
                        "username": connects[int(id.replace("\r","").replace("\n",""))]["username"]
                    })
                    buf = buf.replace("\n", "").replace("\r", "")
                else:
                    buf = prefix + f"""Client {id} Offline."""

            elif ireq[0:10] == "/send-api/":  # /send-api/0/message/114514
                v = ireq.replace("/send-api/", "").split(
                    "/"
                )  # ['0','message','114514']
                v[2] = urllib.parse.unquote(v[2])
                try:
                    messageid = send_message(int(v[0]), v[1], unquote(v[2]))
                    buf = f"Done. NO fallback"
                    for _ in range(20):
                        time.sleep(0.25)
                        try:
                            buf = f"""{base64decode(fallbacks[messageid])}""".replace(
                                "\n", "<br>"
                            )
                            break
                        except KeyError:
                                log("Waiting for fallback ["+messageid+"]")
                        except:
                            log(traceback.format_exc())
                    # print(fallbacks[messageid])
                except ConnectionResetError:
                    connects[int(v[0])]["status"] = False
                    buf = f"""Client Offline."""
            else:
                buf = prefix + " Nothing is here."
        else:
            if ireq[0:14] == "/password-api/":  # /password-api/123456
                ipassword = unquote(
                    ireq.replace("/password-api/", "")
                    .replace("\n", "")
                    .replace("\r", "")
                )
                if ipassword == password:
                    buf = prefix + file("password-yes.html")
                    trusted.append(self.address_string())
                else:
                    buf = prefix + file("password-no.html")
            else:
                buf = prefix + file("password-verify.html").replace("\n", "")
        try:
            self.wfile.write(buf.encode("gb2312"))
        except UnicodeEncodeError:
            self.wfile.write(buf.encode("utf-8"))


def start_web_ui():
    log("web_ui started")
    HTTPServer(("0.0.0.0", server_port[2]), Request).serve_forever()


def start_fallback_server():
    global fallbacks
    global no_fallback_time
    log("fallback_server started")
    while True:
        try:
            s2 = socket.socket()
            s2.bind(("0.0.0.0", server_port[1]))
            s2.listen()
            while True:
                c, addr = s2.accept()
                d = c.recv(10240000).decode("UTF-8")
                # print(d)
                data = d.split("|")
                no_fallback_time = 0
                fallbacks[data[0]] = data[1]
        except:
            log(traceback.format_exc())
            time.sleep(5)


if __name__ == "__main__":
    os.chdir(os.getcwd())
    init_log()
    Thread(target=start_tcp_server).start()
    Thread(target=start_input_thread).start()
    Thread(target=start_web_ui).start()
    Thread(target=start_fallback_server).start()
    Thread(target=no_fallback_time_count).start()
