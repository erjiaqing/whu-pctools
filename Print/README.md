# whu-pctools::Print

WHU程序设计竞赛全家桶-打印服务器

## 依赖

`python3`, `Flask`, `xelatex`

Python3用于支撑服务器，xelatex用于渲染，使用最基本的轮询方式查询，基本能做到秒打印。

**为何不合并入WOJ？**：在举办比赛的时候，我们每年或者每场比赛的时候会使用临时抽调的打印机，为了测试兼容性，另一方面是这个服务编写的时间和新WOJ立项的时间有一些差异，那时WOJ还没有成形，所以使用独立的数据库。

## 运行

在服务器上改一下`_MASTERKEY`，打印机和服务器只靠有效期为30秒的利用masterkey的签名鉴权，理论上能防比赛环境下的攻击。（谁攻击啊）

之后客户端的`masterkey`改的跟服务器的一样，大概对一下时间别差太多。

将用户名和密码导入到`util.db`中，这是一个用sqlite3格式存储的数据库。

服务器上：`python3 server.py`

接打印机的电脑上：`python3 client.py`

## 打印效果

见preview.png