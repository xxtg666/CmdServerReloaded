# CmdServerReloaded

远程cmd控制

## 搭建步骤

### 依赖

Python3

### 启动方法

1. 主控服务器启动`csr-server.py`（设置可在源码前3行中修改）
2. 被控设备启动`csr-client.py`
3. 修改被控设备`csr-client.py`生成的`config.json`，将`server-address`改为主控服务器的ip地址
4. 重新启动被控设备`csr-client.py`
4. 在主控设备打开`http://主控服务器IP:34568/`
5. 在web面板输入主控端密码，点击`Submit`后点击`Verify`（如果有）
6. 找到对应的被控设备，点击`Send`
7. 在顶部的输入框中输入一些东西，点击`Submit`

> 默认密码：`123456`

### 程序配置

csr 的配置分为主控端配置和被控端配置两部分

#### 主控端配置

主控端配置在`csr-server.py`的前三行

```python
server_port = [8631, 8632, 34568]
enable_password = True
password = "123456"
```

| 变量          | 类型          | 备注                |
|---------------|---------------|---------------------|
| `server_port` | `list[str]`   | 服务器端口，第一项为csr TCP端口（对应被控端配置`server-port`），第二项为csr数据回传端口（对应被控端`fallback-server-port`）,第三项为HTTP面板端口 |
| `enable_password` | `bool`    | 是否启用密码，为`False`则`password`变量将被忽略 |
| `password`    | `str`         | HTTP面板密码        |

#### 被控端配置

被控端配置为`config.json`（将在第一次运行`csr-client.py`后创建）

```json
{
  "version": "1.0.0",
  "client-name": "xiaodeng-pc_xiaodeng",
  "local-port": "34567",
  "server-address": "127.0.0.1",
  "server-port": "8631",
  "fallback-server-port": "8632",
  "startup-message-time": "0"
}
```

| 键                        | 类型      | 备注                           |
|---------------------------|-----------|--------------------------------|
| `version`                 | `str`     | 程序版本，请不要修改此项       |
| `client-name`             | `str`     | 被控设备用户名                 |
| `local-port`              | `str`     | 我也不知道这个键是干什么的     |
| `server-address`          | `str`     | 主控服务器IP                   |
| `server-port`             | `str`     | 主控端 csr TCP 端口（对应主控端配置`server_port`第一项） |
| `fallback-server-port`    | `str`     | 主控端 csr 数据回传端口（对应主控端配置`server_port`第二项） |
| `startup-message-time`    | `str`     | 我也不知道这个键是干什么的     |

### 操作说明

- cmd：向被控端发送一条指令并回传`stdout`
- download：向被控端发送一条远程下载指令
- message：在被控设备上弹出一个消息窗（部分环境需要安装`tkinter`依赖）
- python：向被控端发送一条python指令

#### 主控端指令帮助

```bash
=> CmdServerReloaded Server Commands Help
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
exit -- stop server
```

## 鸣谢（排名不分先后）

- [IT Craft Development Team](https://itcdt.top)
