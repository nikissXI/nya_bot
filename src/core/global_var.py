from socket import AF_PACKET, SOCK_RAW, socket

from nonebot.log import logger
from src.models._large_data import Large_data
from ujson import dumps, loads


class GV(object):
    # 异步task强引用
    background_tasks = set()

    # bot变量
    bot_1 = None
    bot_2 = None
    admin_bot = None
    handle_bot = None
    superuser_bot = None
    # key
    secret_key = None

    # 网址
    site_url = None
    # 服务器监听端口
    port = None
    # cdn地址
    cdn_url = None
    # 视频教程链接
    video_url = None
    # 加QQ群链接
    join_group_url = None

    # 网卡名称
    interface_name = None
    # tshark地址
    tshark_path = None
    # wireguard 地址和端口
    wireguard_host = None
    wireguard_port = None
    # wireguard 网关IP
    wireguard_gateway = None
    wireguard_sub_gateway = None
    room_scan_port = None
    # 特殊编号
    r2f = {}
    f2r = {}

    # bot QQ号
    bot_1_num = 0
    bot_2_num = 0
    # 管理员 QQ号
    superuser_num = 0
    # 群号
    miao_group_num = 0
    miao_group2_num = 0
    shencha_group_num = 0
    # 频道ID
    guild_id = 0
    channel_id = 0
    # 喵币系统
    miaobi_system = False
    # 安全模式
    safe_mode = False

    ##########################
    # 缓存数据
    ##########################
    # 运行开始时间
    start_time = 0
    # 发送数据包用的套接字
    send_socket = socket(AF_PACKET, SOCK_RAW)
    # 编号数量总数
    get_wgnum_count = 0
    # 实时联机人数
    online = 0
    # 记录要发送的提示信息
    private_mess = []
    group_mess = []
    channel_mess = []
    # 记录搜房者,防止重复获取 搜索者的IP str   每日重置
    forward_once = {}
    # 记录进群来源   每日重置
    join_check = {}
    # 网页确认身份验证   每日重置
    qq_verified = {}
    # 赞助满30元的加入房间提示列表 {IP str:QQ int}
    vip_ip = {}
    # 好友列表 {QQ int:IP str}
    friendlist = {}
    # 一小时内使用禁言的次数
    jinyan_count = 0
    # 嗅探包数量
    p_count = 0

    ##########################
    # 联机数据
    ##########################
    # 房主特征值 64400200000000000000000000000000 。。。
    host_role = {
        # b"\x7e\x1b\x3c\x24\xf9\xe9\x54\xe7": "权姐",
        # b"\x2f\x21\x10\x5e\x33\x61\x24\xd9": "银藏",
        # b"\xfc\x86\x1d\x43\x2f\x76\xf4\xb3": "法师",
        # b"\xf6\x3c\x3c\xdb\x4b\x83\x84\x5a": "老板",
        # b"\xf9\x23\x72\xe5\x43\x9a\xa4\x34": "女枪",
        # b"\xd1\x7f\x5e\x7a\x9a\xb8\x44\x25": "奥莉",
        # b"\xc8\x25\x81\xf1\xcf\x37\x64\x9d": "钢蛋",
        # b"\xc0\x42\x8c\x73\xb8\x4e\x24\x97": "狂战",
        # b"\x97\x81\x2f\x94\xd9\xb3\x74\x42": "弓手",
        # b"\xae\x88\x44\xf2\x69\xdb\xf4\xfa": "男枪",
        # b"\x85\x60\xf4\x49\x17\xf7\x64\xcf": "黑法",
    }

    # 加房特征值 2d1e 。。。
    join_role = {
        # "2d1e0100000001": "权姐",
        # "2d1e0200000002": "银藏",
        # "2d1e0a00000007": "法师",
        # "2d1e0300000003": "老板",
        # "2d1e5c0000005c": "女枪",
        # "2d1e0500000005": "奥莉",
        # "2d1e0900000006": "钢蛋",
        # "2d1e9500000095": "狂战",
        # "2d1e0400000004": "弓手",
        # "2d1eac000000ac": "男枪",
        # "2d1ebb000000bb": "黑法",
    }
    # { 房主IP str : [ 0:{加入者IP : [角色, 存活]} dict , 1:[已提醒进房提醒的IP] , 2:未定义, 3:存活 int, 4:原始信息 bytes ] ] }
    rooms = {}
    # 房间游戏时间缓存{房主IP str: [开始时间戳 int, 创建时间戳 int]}
    room_time = {}
    # 玩家角色缓存信息{玩家IP str:角色 str}
    role_name = {}
    # 房间自定义名称 {房主IP str:名称 str}
    room_name = {}
    # 专属房  {房主IP str :[允许成员的IP str]}
    privacy = {}
    # 黑名单  {房主IP str :[禁止成员的IP str]}
    black = {}
    # 房间人数上限 {房主IP str:人数 str}
    join_limit = {}
    # 版本设置 {玩家IP str:版本 str}
    version_set = {}

    ##########################
    # 喵币数据
    ##########################
    # 扫雷数据
    saolei_total = 0
    saolei_goal = 0
    saolei_start = 0
    saolei_end = 100
    saolei_once = 0
    saolei_cd = False
    # 随机红包数据
    packet = 0
    packet_log = 0
    packet_once = set()
    # 手动发红数据
    packet_s = 0
    packet_log_s = 0
    packet_once_s = set()
    # 手动发红包的用户名
    packet_username_s = ""
    packet_sender_qqnum = 0

    async def load_some_data(self):
        tmp_host_role = loads(await Large_data.load_host_role())
        for k, v in tmp_host_role.items():
            self.host_role[bytes.fromhex(k)] = v
        self.join_role = loads(await Large_data.load_join_role())
        self.room_time = loads(await Large_data.load_room_time())
        self.role_name = loads(await Large_data.load_role_tmp())
        self.room_name = loads(await Large_data.load_room_name())
        self.privacy = loads(await Large_data.load_privacy())
        self.black = loads(await Large_data.load_black())
        self.join_limit = loads(await Large_data.load_join_limit())
        self.version_set = loads(await Large_data.load_version_set())
        logger.success("联机数据读取成功")

    async def save_some_data(self):
        await Large_data.save_room_play_time(dumps(self.room_time))
        await Large_data.save_role_tmp(dumps(self.role_name))
        await Large_data.save_room_name(dumps(self.room_name))
        await Large_data.save_privacy(dumps(self.privacy))
        await Large_data.save_black(dumps(self.black))
        await Large_data.save_join_limit(dumps(self.join_limit))
        await Large_data.save_version_set(dumps(self.version_set))
        logger.success("联机数据保存成功")

    async def save_role_data(self):
        tmp_host_role = {}
        for k, v in self.host_role.items():
            tmp_host_role[k.hex()] = v
        await Large_data.save_host_role(dumps(tmp_host_role))
        await Large_data.save_join_role(dumps(self.join_role))

    # 单例
    _instance = None

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kw)
        return cls._instance

    def __init__(self):
        pass


gv = GV()
