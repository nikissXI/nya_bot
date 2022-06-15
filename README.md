<div align=center><img height="200" src="https://raw.githubusercontent.com/nikissXI/nya_bot/main/logo.jpg"/></div>

![maven](https://img.shields.io/badge/python-3.10%2B-blue)
![maven](https://img.shields.io/badge/nonebot-2.0.0-yellow)
![maven](https://img.shields.io/badge/go--cqhttp-1.0.0-red)

# nya_bot（喵服）
****
### 喵服是针对战魂铭人这款游戏开发的服务器/bot  
此项目基于 Nonebot2 和 go-cqhttp 开发，以sqlite3作为数据库的战魂铭人远程联机服务器兼QQ机器人，即使脱离QQ机器人也能运行，因为有前端页面。  
有能力的可以修改为其他游戏的联机服务器。

## 关于
代码基本90%都是自己写的，参考了大佬们的代码和意见最后堆出这bot

这个文档是抄[ **[绪山真寻](https://github.com/HibiKier/zhenxun_bot)** ]哒！

logo的图片来自 [ **[nya!](https://www.pixiv.net/artworks/74701713)** ]

战魂铭人远程联机群1047464328 [ **[点击加群](https://jq.qq.com/?_wv=1027&k=bK7UjxJV)** ] [ **[喵服官网](http://nya.nikiss.top)** ]

## 声明
此项目仅用于学习交流，请勿用于非法用途

# Nonebot2
<img style="height: 200px;width: 200px;" src="https://camo.githubusercontent.com/0ef71e86056da694c540790aa4a4e314396884d6c4fdb95362a7538b27a1b034/68747470733a2f2f76322e6e6f6e65626f742e6465762f6c6f676f2e706e67">

非常 [ **[NICE](https://github.com/nonebot/nonebot2)** ] 的OneBot框架

## 命令列表/功能列表

### bot系统命令
* 管理员
  - [√] 状态 —— 查看bot运行状态
  - [√] 网络 —— 获取持续10秒的网络流量数据
  - [√] 喵币系统打开 —— 字面意思（喵币系统命令下面会提到）
  - [√] 喵币系统关闭 —— 字面意思
  - [√] 安全模式打开 —— 字面意思（开了之后会关闭大部分群聊信息，每天0-8点自动开启，防风控）
  - [√] 安全模式关闭 —— 字面意思
  - [√] 中译英xxx —— 翻译功能
  - [√] 英译中xxx —— 翻译功能

### 群管命令
* 所有用户
  - [√] 喵服 —— 打广告！
  - [√] 禁言 —— 群内紧急禁言

* 管理员
  - [√] 搜索 —— 后面接QQ号，搜索目标QQ是否在bot已加的群中
  - [√] 头衔 —— 如果管理员自己当bot可以给头衔
  - [√] 公告列表 —— 字面意思，可以查看公告编号
  - [√] 增加公告 —— 字面意思，内容换行写入
  - [√] 删除公告 —— 后面接公告编号

### 喵币系统命令
* 所有用户
  - [√] 签到 —— 字面意思
  - [√] 喵币 —— 查看自己的喵币余额
  - [√] 转账 —— 将喵币转给其他用户
  - [√] 发红包 —— 发喵币红包
  - [√] 喵币排行 —— 查看喵币排行榜
  - [√] 撸猫 —— 喵币梭哈
  - [√] 概率 —— 查看撸猫概率
  - [√] 扫雷 —— 猜数字
  - [√] 扫雷卡死 —— 扫雷没反应的时候用

* 管理员
  - [√] 喵币总额 —— 查看所有喵币的总额
  - [√] 喵币抹除 —— 删除某用户的喵币信息
  - [√] 设置喵币 —— 修改某用户的喵币余额
  - [√] 增加喵币 —— 增加某用户的喵币余额

### 联机命令（群聊）todo
* 所有用户
  - [√] 签到 —— 字面意思

* 管理员
  - [√] 喵币总额 —— 查看所有喵币的总额

### 联机命令（频道）todo
* 所有用户
  - [√] 签到 —— 字面意思

* 管理员
  - [√] 喵币总额 —— 查看所有喵币的总额

### 联机命令（私聊）todo
* 所有用户
  - [√] 签到 —— 字面意思

* 管理员
  - [√] 喵币总额 —— 查看所有喵币的总额

### 审查组命令todo
* 所有用户
  - [√] 签到 —— 字面意思

* 管理员
  - [√] 喵币总额 —— 查看所有喵币的总额

### 被动功能todo
* 所有用户
  - [√] 签到 —— 字面意思

* 管理员
  - [√] 喵币总额 —— 查看所有喵币的总额

## 部署

```
# 前排提醒
本bot仅支持在Linux系统上运行，因为wireguard服务器我只会在Linux上部署！

# 下载配置go-cqhttp
在 https://github.com/Mrs4s/go-cqhttp 下载Releases最新版本，运行后选择反向代理，
  后将gocq的配置文件config.yml中的universal改为
  universal: ws://127.0.0.1:80/onebot/v11/ws 
  如果.env里改了其他端口这里跟着改啊，灵活点！

# 获取代码
git clone https://github.com/nikissXI/nya_bot.git
或者直接下载zip解压一样

# 然后安装软件
Ubuntu系统可以输入以下命令
apt install wireguard tshark

其他系统安装
wireguard参考它的官网 https://www.wireguard.com/install/
tshark就百度啦，一大堆

# 安装依赖
pip install nb-cli nonebot-adapter-onebot apscheduler pillow tortoise-orm psutil ujson
我不会虚拟环境啊啊啊啊啊啊啊啊啊

# 开放端口
需要开放端口机器人的监听端口，类型TCP，不然外网访问不了网页
还有wireguard的监听端口，类型UDP，不然wireguard客户端连不上

# 进入目录
cd nya_bot

# 开始运行
python bot.py 或 nb run
```

## 配置

```
自己打开.env文件看着注释填哈，QQ群自己创建
```

## 更新

### 2022/6/15 \[v1.0.0]

* 将机器人开源，发布到github


## 致谢
NoneBot交流群 768887710，群除我佬，感谢各位大佬的帮助  
感谢各位战魂铭人玩家的支持  [ **[赞助榜](http://nya.nikiss.top/sponsor)** ]  
[botuniverse / onebot](https://github.com/botuniverse/onebot) ：超棒的机器人协议  
[Mrs4s / go-cqhttp](https://github.com/Mrs4s/go-cqhttp) ：cqhttp的golang实现，轻量、原生跨平台.  
[nonebot / nonebot2](https://github.com/nonebot/nonebot2) ：跨平台Python异步机器人框架