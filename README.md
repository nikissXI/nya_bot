<div align=center><img width="600" src="https://raw.githubusercontent.com/nikissXI/nya_bot/main/logo.jpg"/>

![maven](https://img.shields.io/badge/python-3.10%2B-blue)
![maven](https://img.shields.io/badge/nonebot-2.0.0-yellow)
![maven](https://img.shields.io/badge/go--cqhttp-1.0.0-red)
[![OSCS Status](https://www.oscs1024.com/platform/badge/nikissXI/nya_bot.svg?size=small)](https://www.oscs1024.com/project/nikissXI/nya_bot?ref=badge_small)
</div>

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

#### bot系统命令
* 管理员
  - [√] 状态 —— 查看bot运行状态
  - [√] 网络 —— 获取持续10秒的网络流量数据
  - [√] 喵币系统打开 —— 字面意思（喵币系统命令下面会提到）
  - [√] 喵币系统关闭 —— 字面意思
  - [√] 安全模式打开 —— 字面意思（开了之后会关闭大部分群聊信息，每天0-8点自动开启，防风控）
  - [√] 安全模式关闭 —— 字面意思
  - [√] 中译英 —— 翻译功能，后面接要翻译的内容
  - [√] 英译中 —— 翻译功能，后面接要翻译的内容

#### 群管命令
* 所有用户
  - [√] 喵服 —— 打广告！
  - [√] 禁言 —— 群内紧急禁言

* 管理员
  - [√] 搜索 —— 后面接QQ号，搜索目标QQ是否在bot已加的群中
  - [√] 头衔 —— 如果管理员自己当bot可以给头衔
  - [√] 公告列表 —— 字面意思，可以查看公告编号
  - [√] 增加公告 —— 字面意思，内容换行写入
  - [√] 删除公告 —— 后面接公告编号

#### 喵币系统命令
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

#### 联机服务器命令
* 所有用户（群聊）
  - [√] 验证 —— 领号的时候用的
  - [√] 帮助 —— 查看命令列表（只显示常用的，具体有：查房、官网、教程、升级、后台、排行、黑名单、频道、文章、赞助）

* 所有用户（频道）
  - [√] 帮助 —— 查看命令列表（在群聊命令的基础上有下面这些）
  - [√] 检测 —— 检测连接情况和网络延迟
  - [√] 查绑 —— 查询编号绑定状态
  - [√] 找卡比 —— 看看房间里的玩家网络延迟情况

* 所有用户（好友私聊）
  - [√] 帮助 —— 查看命令列表（上面群聊和频道的命令都能用，并且有额外的，这里不细说）

* 管理员
  - [√] 角色改名 —— 修改游戏角色显示的名字
  - [√] 未绑定 —— 查看未绑定的编号
  - [√] 非赞助 —— 查看非赞助的编号
  - [√] 特殊编号 —— 查看特殊编号
  - [√] QQ 绑定 —— 为该QQ号随机绑定一个未绑定编号或升级到普通号
  - [√] QQ 编号 特绑 —— 为该QQ号绑定一个指定编号并升级到普通号
  - [√] 解绑 QQ —— 解绑该QQ号绑定的编号
  - [√] 赞助 QQ 金额 —— 为该QQ号添加赞助信息并升级到赞助号，金额如果为0则是删除赞助信息
  - [√] 赞助总额 —— 查看赞助榜总额
  - [√] 修罗 编号 数值 —— 将该编号上修罗之力排行榜
  - [√] ban —— 禁止领取体验号
  - [√] 扩容 数值 —— 扩大编号到指定数值
  - [√] 缩容 数值 —— 缩减编号到指定数值
  - [√] 重载 —— reload该编号的隧道信息，一般用不上

#### 审查组命令
* 审查组成员
  - 注：管理审查组成员需要到网页的服主后台操作
  - [√] 破解留言 —— 字面意思
  - [√] 高修留言 —— 字面意思
  - [√] 流程图 —— 显示审查流程图
  - [√] 待审查 —— 查看待审查列表
  - [√] 查绑 QQ —— 查询该QQ绑定信息
  - [√] 扫描 —— 扫描黑名单是否在bot加入的群里
  - [√] 审查 QQ或编号 —— 将目标禁言并加入待审查列表
  - [√] 解禁 —— 解除禁言并从待审查列表移除
  - [√] 踢出 —— 踢出群

#### 被动功能
  - [√] 支持双bot冗余 —— 如果双bot运行，命令会各负责一半，如果其中一个掉了另一个自动顶上
  - [√] 防闪照 —— 机器人检测到闪照就会把图片私发给管理员（所有群）
  - [√] 防撤回 —— 机器人检测到撤回就会把内容私发给管理员（仅支持联机群）
  - [√] 自动同意进群 —— 字面意思（仅联机群）
  - [√] 进退群提示 —— 字面意思（仅联机群）
  - [√] 自动通过好友 —— 需要赞助号身份的QQ，否则自动拒绝
  - [√] 自动清理潜水员 —— 联机群一个月不说话且没编号的就会踢出去
  - [√] 强制新人阅读群规 —— 新人进群禁言一个月，不阅读群规不解禁

#### 网页
  - [√] 长啥样自己去我官网看啦 [ **[喵服官网](http://nya.nikiss.top)** ]
  - [√] 网页里服主后台的key就是.env里面的onebot_access_token

#### 战魂铭人远程联机功能介绍
  - [√] 使用wireguard进行组网，相比其他组网软件，它能带来最稳定、最方便的联机体验
  - [√] 安卓的wireguard客户端已进行修改，在目录www/static/cdn中（根据网页的操作就能下载），能通过服务器自动导入配置，其他的还是用官方原版客户端
  - [√] 联机编号全自动管理 —— 这个得搞联机的服主才有感觉（比如我）
  - [√] 能返回游戏房间列表并识别玩家使用的游戏角色
  - [√] 支持游戏房间某些自定义，如房间名称、人数上限、版本号
  - [√] 比较杂，不列啦！

## 部署

```
# 前排提醒
本bot仅支持在Linux系统上运行，因为wireguard服务器我只会在Linux上部署！并且要用root权限运行，因为用到了原始套接字编程。

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
apt install wireguard tshark qrencode

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

### 2022/7/7 \[v1.2.0]

* 增加新人进群禁言功能，需要阅读群规才能解除禁言
* asyncio.create_task改为强引用
* 解决关闭bot时有个await sleep的报错（用asyncio.call_later解决了）
* 其他局部小优化

### 2022/6/25 \[v1.1.0]

* 增加新人进群禁言功能，需要阅读群规才能解除禁言
* asyncio.create_task改为强引用
* 解决关闭bot时有个await sleep的报错（用asyncio.call_later解决了）
* 其他局部小优化

### 2022/6/15 \[v1.0.0]

* 将机器人开源，发布到github


## 致谢
NoneBot交流群 768887710，群除我佬，感谢各位大佬的帮助  
感谢各位战魂铭人玩家的支持  [ **[赞助榜](http://nya.nikiss.top/sponsor)** ]  
[botuniverse / onebot](https://github.com/botuniverse/onebot) ：超棒的机器人协议  
[Mrs4s / go-cqhttp](https://github.com/Mrs4s/go-cqhttp) ：cqhttp的golang实现，轻量、原生跨平台.  
[nonebot / nonebot2](https://github.com/nonebot/nonebot2) ：跨平台Python异步机器人框架
