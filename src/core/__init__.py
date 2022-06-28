from asyncio import create_task, sleep
from datetime import datetime
from math import sqrt
from random import randint
from re import S, compile, sub

from httpx import AsyncClient
from nonebot import get_driver, on_message, on_notice, on_regex, on_request
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11.event import (
    FriendAddNoticeEvent,
    FriendRequestEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    GroupRecallNoticeEvent,
    GroupRequestEvent,
    MessageEvent,
    NoticeEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.log import logger
from src.models._gold import Gold
from src.models._large_data import Large_data
from src.models._little_data import Little_data
from src.models._nofree import Nofree
from src.models._shencha import Shencha
from src.models._sponsor import Sponsor
from src.models._tips import Tips
from src.models._wg import Wg
from src.models._zhb_list import Zhb_list
from src.models._zhb_user import Zhb_user
from tortoise import Tortoise
from ujson import loads

from .channel_patch import GuildMessageEvent
from .config import (
    bd_api,
    black_api,
    jb_api,
    join_limit_api,
    krsr_api,
    privacy_api,
    room_name_api,
    version_set_api,
    xl_api,
    zz_api,
)
from .global_var import gv
from .scheduler import start_scheduler
from .sniff import start_sniff
from .utils import (
    check_group_zhb,
    check_in_group,
    exec_shell,
    get_group_name,
    get_net_io,
    get_qqnum_nickname,
    get_room_list,
    handle_exception,
    ip_to_wgnum,
    network_status,
    server_status,
    wgnum_to_ip,
)
from .web import start_web_server
from .wgnum import check_num, get_wgnum_count, refresh_friendlist, release_wgnum

#################################
# 框架操作
#################################
driver = get_driver()

# 启动时执行
@driver.on_startup
async def do_startup():
    gv.start_time = datetime.now()
    try:
        config = driver.config
        gv.port = config.port
        gv.secret_key = config.onebot_access_token
        gv.site_url = config.site_url
        gv.cdn_url = config.cdn_url
        gv.video_url = config.video_url
        gv.join_group_url = config.join_group_url
        gv.bot_1_num = str(config.bot_1_num)
        gv.bot_2_num = str(config.bot_2_num)
        gv.superuser_num = config.superuser_num
        gv.interface_name = config.interface_name
        gv.tshark_path = config.tshark_path
        gv.wireguard_host = config.wireguard_host
        gv.wireguard_port = config.wireguard_port
        gv.wireguard_gateway = config.wireguard_gateway
        gv.room_scan_port = config.room_scan_port
        a, b, c, d = gv.wireguard_gateway.split(".")
        gv.wireguard_sub_gateway = f"{a}.{b}"
        gv.miao_group_num = config.miao_group_num
        gv.miao_group2_num = config.miao_group2_num
        gv.shencha_group_num = config.shencha_group_num
        gv.guild_id = config.guild_id
        gv.channel_id = config.channel_id
        special_wgnum = eval(config.special_wgnum)
        if special_wgnum:
            for k, v in special_wgnum.items():
                gv.r2f[k] = v
                gv.f2r[v] = k
        logger.success("加载配置成功")
    except Exception:
        logger.error("加载配置失败")

    # 连接sqlite3数据库
    models = [
        "src.models._gold",
        "src.models._sponsor",
        "src.models._tips",
        "src.models._visit",
        "src.models._wg",
        "src.models._xl",
        "src.models._zhb_list",
        "src.models._zhb_user",
        "src.models._guide",
        "src.models._nofree",
        "src.models._large_data",
        "src.models._little_data",
        "src.models._shencha",
    ]
    await Tortoise.init(
        db_url=f"sqlite://data/data.db",
        modules={"models": models},
    )
    await Tortoise.generate_schemas()
    logger.success("数据库连接成功")

    # 初始化数据
    await Large_data.data_reset()
    await Little_data.data_reset()
    await gv.load_some_data()
    await get_wgnum_count()
    gv.miaobi_system = await Little_data.get_miaobi_system()
    gv.safe_mode = await Little_data.get_safe_mode()

    # 0-8点开启安全模式
    if gv.safe_mode is False:
        if not 8 <= datetime.now().hour <= 23:
            gv.safe_mode = await Little_data.update_safe_mode(1)

    try:
        gv.send_socket.bind(("miao", 0))
    except Exception:
        logger.error("未发现WG网卡，尝试启动...")
        code, stdout, stderr = await exec_shell(
            f"bash src/shell/wg_up.sh {gv.wireguard_gateway} {gv.wireguard_port}"
        )
        if code:
            exit("WG网卡绑定失败，无法启动服务器")
        else:
            gv.send_socket.bind(("miao", 0))
            # 首次启动网卡时加载编号配置进入wg
            for wgnum in range(1, gv.get_wgnum_count + 1):
                code, stdout, stderr = await exec_shell(
                    f"bash src/shell/wg_renew.sh insert {gv.wireguard_host} {gv.wireguard_port} {gv.wireguard_sub_gateway} {wgnum_to_ip(wgnum)}"
                )
            # 保存配置文件
            await exec_shell(f"bash src/shell/wg_renew.sh save")
            logger.success(f"成功从配置文件导入并加载编号{gv.get_wgnum_count}个")

    def _create_background_task(_def, _name):
        task = create_task(_def, name=_name)
        gv.background_tasks.add(task)
        task.add_done_callback(gv.background_tasks.discard)

    # 启动定时任务模块
    _create_background_task(start_scheduler(), "scheduler_task")
    # 启动网页服务模块
    _create_background_task(start_web_server(), "web_task")
    # 启动流量嗅探模块
    _create_background_task(start_sniff(), "sniff_task")

    logger.success(f"安全模式: {gv.safe_mode}")
    logger.success(f"喵币系统: {gv.miaobi_system}")
    logger.success(f"启动完毕！等待go-cqhttp连接...")
    logger.success(
        "\n\
  _   ___     __       \n\
 | \ | \ \   / //\     \n\
 |  \| |\ \_/ //  \    \n\
 | . ` | \   // /\ \   \n\
 | |\  |  | |/ ____ \  \n\
 |_| \_|  |_/_/    \_\ v1.1.0\n\
Dev by nikiss <1299577815@qq.com>\n"
    )


# 关闭时执行
@driver.on_shutdown
async def do_shutdown():
    gv.p_count = 1000000
    if gv.packet_s > 0:
        await Gold.change_money(gv.packet_sender_qqnum, gv.packet_s, True)
        logger.success(f"{gv.packet_username_s}发的红包还有{gv.packet_s}个未分完，已返还")
    logger.success("等待世界线收缩...")
    await sleep(1)
    await gv.save_some_data()
    await Tortoise.close_connections()
    logger.success(
        "\n\
  ______     ________  \n\
 |  _ \ \   / /  ____| \n\
 | |_) \ \_/ /| |__    \n\
 |  _ < \   / |  __|   \n\
 | |_) | | |  | |____  \n\
 |____/  |_|  |______| \n"
    )


def bot_switch():
    if gv.bot_1 is not None:
        gv.admin_bot = gv.bot_1
    elif gv.bot_2 is not None:
        gv.admin_bot = gv.bot_2
    else:
        gv.admin_bot = None

    if gv.bot_2 is not None:
        gv.handle_bot = gv.bot_2
    elif gv.bot_1 is not None:
        gv.handle_bot = gv.bot_1
    else:
        gv.handle_bot = None


# qq机器人连接时执行
@driver.on_bot_connect
async def on_bot_connect_handle(bot: Bot):
    if bot.self_id == gv.bot_1_num:
        gv.bot_1 = bot
        await refresh_friendlist()

    elif bot.self_id == gv.bot_2_num:
        gv.bot_2 = bot

    elif bot.self_id == str(gv.superuser_num):
        gv.superuser_bot = bot

    bot_switch()
    logger.success(f"{bot.self_id}上线")
    await sleep(3)
    gv.private_mess.append((gv.superuser_num, f"{bot.self_id}上线"))


# qq机器人断开时执行
@driver.on_bot_disconnect
async def on_bot_disconnect_handle(bot: Bot):
    if bot.self_id == gv.bot_1_num:
        gv.bot_1 = None
        await refresh_friendlist()

    elif bot.self_id == gv.bot_2_num:
        gv.bot_2 = None
    elif bot.self_id == str(gv.superuser_num):
        gv.superuser_bot = None

    bot_switch()
    logger.error(f"{bot.self_id}离线")
    await sleep(3)
    gv.private_mess.append((gv.superuser_num, f"{bot.self_id}离线"))


#################################
# QQ消息类型过滤器
#################################
# 喵服验证
async def group_check_special(event: GroupMessageEvent, bot: Bot) -> bool:
    if event.group_id == gv.miao_group_num or event.group_id == gv.miao_group2_num:
        if gv.bot_1 is not None:
            return bot.self_id == gv.bot_1_num
        else:
            return bot.self_id == gv.bot_2_num
    else:
        return False


# 战魂联机群消息
async def zhanhun_group_check(event: GroupMessageEvent, bot: Bot) -> bool:
    if gv.safe_mode:
        return False
    elif event.group_id == gv.miao_group_num:
        if gv.bot_2 is not None:
            return bot.self_id == gv.bot_2_num
        else:
            return bot.self_id == gv.bot_1_num
    else:
        return False


# 审查群消息
async def shencha_group_check(event: GroupMessageEvent, bot: Bot) -> bool:
    if event.group_id == gv.shencha_group_num or event.group_id == gv.miao_group_num:
        if gv.bot_1 is not None:
            return bot.self_id == gv.bot_1_num
        else:
            return bot.self_id == gv.bot_2_num
    else:
        return False


# 喵币签到专用
async def miaobi_check_qiandao(event: GroupMessageEvent, bot: Bot) -> bool:
    if event.group_id == gv.miao_group_num or event.group_id == gv.miao_group2_num:
        if gv.bot_1 is not None:
            return bot.self_id == gv.bot_1_num
        else:
            return bot.self_id == gv.bot_2_num
    else:
        return False


# 喵币使用群
async def miaobi_check(event: GroupMessageEvent, bot: Bot) -> bool:
    if gv.safe_mode:
        return False
    elif event.group_id == gv.miao_group_num or event.group_id == gv.miao_group2_num:
        if gv.miaobi_system:
            return bot.self_id == gv.bot_1_num
        else:
            return False
    else:
        return False


# 判断bot
async def bot_1_event(bot: Bot) -> bool:
    return bot.self_id == gv.bot_1_num


async def bot_2_event(bot: Bot) -> bool:
    return bot.self_id == gv.bot_2_num


# bot自动切换
async def auto_bot(bot: Bot) -> bool:
    if gv.bot_1 is not None:
        return bot.self_id == gv.bot_1_num
    elif gv.bot_2 is not None:
        return bot.self_id == gv.bot_2_num
    else:
        return False


# bot自动切换（管理员）
async def auto_bot_superuser(event: MessageEvent, bot: Bot) -> bool:
    if event.user_id != gv.superuser_num:
        return False
    elif gv.bot_1 is not None:
        return bot.self_id == gv.bot_1_num
    elif gv.bot_2 is not None:
        return bot.self_id == gv.bot_2_num
    else:
        return False


# 频道消息
async def guild_check(event: GuildMessageEvent, bot: Bot) -> bool:
    if event.guild_id == gv.guild_id and event.channel_id == gv.channel_id:
        if gv.bot_2 is not None:
            return bot.self_id == gv.bot_2_num
        elif gv.bot_1 is not None:
            return bot.self_id == gv.bot_1_num
    else:
        return False


#################################
# 事件处理
#################################
# 审查目标活跃监听
# listen_all = on_message(rule=bot_1_event)
# 闪照检测
anti_flash = on_message(rule=auto_bot)
# 撤回检测
recall_notice = on_notice(rule=bot_1_event)
# 进群、退群处理
group_notice = on_notice(rule=auto_bot)
# 加群请求
group_req = on_request(rule=auto_bot)
# 加好友请求
friend_req = on_request(rule=bot_1_event)
# 好友增加处理
new_friend = on_notice(rule=bot_1_event)

#################################
# 管理员命令
#################################
# 测试命令
test = on_regex("^测试$", rule=auto_bot_superuser)
fasong = on_regex("^发送", rule=auto_bot_superuser)

# bot系统命令
zhuangtai = on_regex("^状态$", rule=auto_bot_superuser)
wangluo = on_regex("^网络$", rule=auto_bot_superuser)
miaobixitong = on_regex("^喵币系统打开$|^喵币系统关闭$", rule=auto_bot_superuser)
anquanmoshi = on_regex("^安全模式打开$|^安全模式关闭$", rule=auto_bot_superuser)
zhongyiying = on_regex("^中译英", rule=auto_bot_superuser)
yingyizhong = on_regex("^英译中", rule=auto_bot_superuser)

#################################
# 群管命令
#################################
# 所有用户
miaofu = on_regex("^喵服$", rule=auto_bot)
jinyan = on_regex("^禁言\s*\d{1,}$|^禁言$", rule=group_check_special)

# 管理员
sousuo = on_regex("^搜索\s*\d+$", rule=auto_bot_superuser)
touxian = on_regex("^头衔\s*\d+\s+", rule=auto_bot_superuser)
gonggaoliebiao = on_regex("^公告列表$", rule=auto_bot_superuser)
zengjiagonggao = on_regex("^增加公告", rule=auto_bot_superuser)
shanchugonggao = on_regex("^删除公告\s*\d{1,}$", rule=auto_bot_superuser)

#################################
# 喵币系统命令
#################################
# 所有用户
qiandao = on_regex("^签到$", rule=miaobi_check_qiandao)
miaobi = on_regex("^喵币$", rule=miaobi_check)
zhuanzhang = on_regex("^转账\s*\d+\s+\d+$|^转账$", rule=miaobi_check)
fahongbao = on_regex("^发红包\s*\d+$|^发红包$", rule=miaobi_check)
qiangmiaobi = on_regex("^抢喵币$", rule=miaobi_check)
miaobipaihang = on_regex("^喵币排行$", rule=miaobi_check)
lumao = on_regex("^撸猫$", rule=miaobi_check)
gailv = on_regex("^概率$", rule=miaobi_check)
saolei_h = on_regex("^扫雷$", rule=miaobi_check)
saolei = on_regex("^扫雷\s*[0-9]{1,3}$", rule=miaobi_check)
saoleikasi = on_regex("^扫雷卡死$", rule=miaobi_check)

# 管理员
miaobizonge = on_regex("^喵币总额$", rule=auto_bot_superuser)
miaobimochu = on_regex("^喵币抹除\s*\d+$|^喵币抹除$", rule=auto_bot_superuser)
shezhimiaobi = on_regex("^设置喵币\s*\d+\s+\d+$|^设置喵币$", rule=auto_bot_superuser)
zengjiamiaobi = on_regex("^增加喵币\s*\d+\s+\d+$|^增加喵币$", rule=auto_bot_superuser)

#################################
# 联机服务器命令
#################################
# 所有用户（群聊）
yanzheng = on_regex("^验证$", rule=group_check_special)
link = on_regex(
    "^帮助$|^官网$|^教程$|^升级$|^后台$|^排行$|^黑名单$|^频道$|^文章$|^赞助$|^群规$", rule=zhanhun_group_check
)
chafang = on_regex("^查房$", rule=auto_bot)

# 所有用户（频道）
cchafang = on_regex("^查房$", rule=guild_check)
clink = on_regex("^帮助$|^官网$|^后台$|^排行$|^赞助$|^黑名单$|^教程$|^文章$|^升级$|^领号$", rule=guild_check)
cjiance = on_regex("^检测\s*\d+$|^检测$", rule=guild_check)
czhaokabi = on_regex("^找卡比\s*\d+$|^找卡比$", rule=guild_check)
cchabang = on_regex("^查绑\s*\d{1,}$|^查绑$", rule=guild_check)

# 所有用户（好友私聊）
pbangzhu = on_regex("^帮助$", rule=bot_1_event)
pchafang = on_regex("^查房$", rule=bot_1_event)
plink = on_regex("^官网$|^后台$|^排行$|^赞助$|^黑名单$|^教程$|^文章$|^升级$|^领号$", rule=bot_1_event)
pchabang = on_regex("^查绑\s*\d{1,}$|^查绑$", rule=bot_1_event)
pjiance = on_regex("^检测\s*\d+$|^检测$", rule=bot_1_event)
pzhaokabi = on_regex("^找卡比\s*\d+$|^找卡比$", rule=bot_1_event)
peizhi = on_regex("^配置$|^配置\s*\d+$", rule=bot_1_event)
fangming = on_regex("^房名", rule=bot_1_event)
siyou = on_regex("^私有", rule=bot_1_event)
lahei = on_regex("^拉黑", rule=bot_1_event)
renshu = on_regex("^人数", rule=bot_1_event)
banben = on_regex("^版本", rule=bot_1_event)

# 管理员
juesegaiming = on_regex("^角色改名", rule=auto_bot_superuser)
weibangding = on_regex("^未绑定$", rule=auto_bot_superuser)
feizanzhu = on_regex("^非赞助$", rule=auto_bot_superuser)
teshubianhao = on_regex("^特殊编号$", rule=auto_bot_superuser)
bangding = on_regex("^\d+\s*绑定$|^\d+\s+\d+\s*特绑$", rule=auto_bot_superuser)
jiebang = on_regex("^解绑\s*\d+$", rule=auto_bot_superuser)
zanzhu = on_regex("^赞助\s*\d+\s+[\+\-]?\d+$", rule=auto_bot_superuser)
xiuluo = on_regex("^修罗\s*\d+\s+\d+$", rule=auto_bot_superuser)
kuorong = on_regex("^扩容\s*\d+$|^缩容\s*\d+$", rule=auto_bot_superuser)
chongzai = on_regex("^重载\s*\d+$", rule=auto_bot_superuser)
baipiao = on_regex("^白嫖\s*-?\d+$|^白嫖$", rule=auto_bot_superuser)
zanzhuzonge = on_regex("^赞助总额$", rule=auto_bot_superuser)


#################################
# 审查组命令
#################################
pojieliuyan = on_regex("^破解留言$", rule=shencha_group_check)
gaoxiuliuyan = on_regex("^高修留言$", rule=shencha_group_check)
liuchengtu = on_regex("^流程图$", rule=shencha_group_check)
daishencha = on_regex("^待审查$", rule=shencha_group_check)
chabang = on_regex("^查绑\s*\d{1,}$|^查绑$", rule=shencha_group_check)
saomiao = on_regex("^扫描$", rule=shencha_group_check)
shencha = on_regex("^审查\s*\d{1,}$|^审查$", rule=shencha_group_check)
jiejin = on_regex("^解禁\s*\d{1,}$", rule=shencha_group_check)
tichu = on_regex("^踢出\s*\d+$|^永拒\s*\d+$|^踢出$", rule=shencha_group_check)


#################################
# 频道命令
#################################
@cchafang.handle()
@handle_exception("频道查房", True)
async def handle_cchafang():
    await cchafang.finish(await get_room_list())


@clink.handle()
@handle_exception("频道link", True)
async def handle_clink(event: GuildMessageEvent):
    mess_dict = {
        "帮助": f"【支持的命令有以下】\n领号|升级|赞助|排行|黑名单\n教程|后台|查绑|查房|找卡比",
        "官网": f"喵服官网(联机教程)：{gv.site_url}",
        "教程": f"文字教程：{gv.site_url}/config\n视频教程：{gv.video_url}",
        "后台": f"玩家后台：{gv.site_url}/bk",
        "排行": f"喵服修罗之力排行榜：{gv.site_url}/xl",
        "赞助": f"喵服赞助名单：{gv.site_url}/sponsor",
        "黑名单": f"黑名单：{gv.site_url}/zhb",
        "文章": f"文章列表：{gv.site_url}/guide",
        "领号": f"领号页面：{gv.site_url}/get",
        "升级": f"升级编号：{gv.site_url}/get?x",
    }
    kw = str(event.get_message()).replace("\n", "")
    await link.finish(mess_dict[kw])


@cjiance.handle()
@handle_exception("频道检测", True)
async def handle_cjiance(event: GuildMessageEvent):
    if str(event.get_message()) == "检测":
        await cjiance.finish("检测+编号")
    else:
        wgnum = int(str(event.get_message())[2:].strip())
        msg = await network_status(wgnum, 1)
        if msg.find("ms") == -1:
            await cjiance.finish(msg)
        else:
            await cjiance.send(msg.replace("<br />", "\n"))
        msg = await network_status(wgnum, 2)
        await cjiance.finish(msg.replace("<br />", "\n"))


@czhaokabi.handle()
@handle_exception("频道找卡比", True)
async def handle_czhaokabi(event: GuildMessageEvent):
    if str(event.get_message()) == "找卡比":
        await czhaokabi.finish("找卡比+编号")
    else:
        wgnum = int(str(event.get_message())[3:].strip())
        await czhaokabi.send("查询中，请稍后...")
        msg = await network_status(wgnum, 3)
        await czhaokabi.finish(msg.replace("<br />", "\n"))


@cchabang.handle()
@handle_exception("频道查绑", True)
async def handle_cchabang(event: GuildMessageEvent):
    if str(event.get_message()) == "查绑":
        await cchabang.finish("查绑+编号或Q号")
    else:
        num = int(str(event.get_message())[2:].strip())
        msg = await check_num(num)
        msg = msg.replace("<br />", "\n")
        await cchabang.finish(msg)


#################################
# 公共命令
#################################
@miaofu.handle()
@handle_exception("喵服宣传")
async def handle_miaofu(event: GroupMessageEvent):
    if gv.safe_mode is False:
        await miaofu.finish(
            f"战魂铭人远程联机平台-喵服\n教程: {gv.video_url}\n"
            + MessageSegment.image(
                "https://img2.tapimg.com/bbcode/etag/lnxAi1YkbinAy4wLuiM207lWODp-.gif"
            )
        )


#################################
# 事件处理
#################################
@anti_flash.handle()
@handle_exception("闪照")
async def handle_anti_flash(event: GroupMessageEvent):
    msg = str(event.get_message())
    if "image" in msg and "flash" in msg:
        text = compile(r"file=(.*?).image", S)
        text = str(text.findall(msg))
        reg = "[^0-9A-Za-z\u4e00-\u9fa5]"
        x = str(sub(reg, "", text.upper()))
        id = "2042064460"
        url = (
            "https://gchat.qpic.cn/gchatpic_new/"
            + id
            + "/2640570090-2264725042-"
            + x.upper()
            + "/0?term=3"
        )

        await gv.admin_bot.send_private_msg(
            user_id=gv.superuser_num,
            message=f"{event.sender.nickname}({event.sender.user_id})发送了闪照\n\n"
            + MessageSegment.image(url),
        )


@recall_notice.handle()
@handle_exception("撤回")
async def handle_req_event(event: GroupRecallNoticeEvent):
    if (
        (
            event.group_id == gv.miao_group_num
            or event.group_id == gv.miao_group2_num
            or event.group_id == gv.shencha_group_num
        )
        and event.operator_id == event.user_id
        and gv.admin_bot is not None
    ):
        res = await gv.admin_bot.get_msg(message_id=event.message_id)
        if "flash" not in str(res["message"]):
            await gv.admin_bot.send_private_msg(
                user_id=gv.superuser_num,
                message=f'{res["sender"]["nickname"]}({res["sender"]["user_id"]})撤回如下内容\n\n'
                + res["message"],
            )


# @listen_all.handle()
# async def handle_listen_all(event: GroupMessageEvent):
#     if (
#         await Shencha.qqnum_exist(event.user_id)
#         and event.group_id != gv.shencha_group_num
#     ):
#         groupname = await get_group_name(event.group_id)
#         gv.group_mess.append(
#             (
#                 gv.shencha_group_num,
#                 f"待审查目标活跃提醒\n{groupname}({event.group_id})\n{await Shencha.get_one(event.user_id)}",
#             )
#         )


@group_req.handle()
@handle_exception("加群请求")
async def handle_req_event(event: GroupRequestEvent):
    if event.group_id == gv.miao_group_num:
        gv.join_check[event.user_id] = event.comment[event.comment.find("答案") + 3 :]
        try:
            await sleep(randint(10, 30))
            await event.approve(gv.admin_bot)
        except Exception:
            logger.error("消息已被处理")


@friend_req.handle()
@handle_exception("加好友请求")
async def handle_req_event(event: FriendRequestEvent):
    await sleep(randint(10, 30))
    if await Sponsor.vip_exist(event.user_id):
        await event.approve(gv.bot_1)
    else:
        await event.reject(gv.bot_1)


@new_friend.handle()
@handle_exception("新增好友")
async def handle_new_friend(event: FriendAddNoticeEvent):
    await sleep(3)
    await refresh_friendlist()
    if event.user_id in gv.friendlist.keys():
        await new_friend.finish(
            MessageSegment.image(f"{gv.site_url}/static/friend.gif")
            + "感谢您的赞助\n发送“帮助”可查看命令"
        )


@group_notice.handle()
@handle_exception("群通知")
async def handle_group_notice(event: NoticeEvent):
    await sleep(3)
    if isinstance(event, GroupDecreaseNoticeEvent):
        qqnum = event.user_id
        # 退出联机群
        if event.group_id == gv.miao_group_num:
            if qqnum in gv.qq_verified.keys():
                gv.qq_verified.pop(qqnum)
            if await Shencha.qqnum_exist(qqnum):
                gv.group_mess.append(
                    (
                        gv.shencha_group_num,
                        f"被审查目标退群，该记录已移除\n{await Shencha.get_one(qqnum)}",
                    )
                )
                await Shencha.delete_qqnum(qqnum)

            if await Wg.num_bind(qqnum):
                await release_wgnum(qqnum, True)

            nickname = await get_qqnum_nickname(qqnum)
            if event.sub_type == "kick":
                t = "获得奖励"
                img = "kick.jpg"
            else:
                t = "退群了"
                img = "bye.jpg"
            await group_notice.finish(
                f"{nickname}({qqnum}){t}"
                + MessageSegment.image(f"{gv.site_url}/static/{img}")
            )

        # 判断是否在黑名单
        elif (
            event.group_id != gv.miao_group2_num
            and event.group_id != gv.shencha_group_num
            and qqnum in await Zhb_list.get_all_qq()
        ):
            nickname = await get_qqnum_nickname(qqnum)
            groupname = await get_group_name(event.group_id)
            gv.group_mess.append(
                (
                    gv.shencha_group_num,
                    f"黑名单清理提醒\n{nickname}({qqnum})\n{groupname}({event.group_id})",
                )
            )

    elif isinstance(event, GroupIncreaseNoticeEvent):
        qqnum = event.user_id
        ######## 喵服群 ###########
        if event.group_id == gv.miao_group_num:

            # 判断是否在黑名单
            if qqnum in await Zhb_list.get_all_qq():
                await group_notice.finish(
                    MessageSegment.at(qqnum)
                    + f"黑名单中有你份，原因请看\n{gv.site_url}/why?qq={qqnum}"
                )

            # 不在黑名单就欢迎
            else:
                try:
                    come_from = gv.join_check[qqnum]
                except KeyError:
                    come_from = "获取失败"  # "功能暂时关闭"
                if qqnum in gv.join_check.keys():
                    gv.join_check.pop(qqnum)

                # 检查是否以前进来过
                if await Gold.get_read_flag(qqnum) == 1:
                    await group_notice.finish(
                        MessageSegment.at(qqnum)
                        + f"欢迎回来！\n来源: {come_from}\n"
                        + MessageSegment.image(f"{gv.site_url}/static/welcome.gif")
                    )

                # 新人欢迎
                else:
                    await Gold.create_info(qqnum)
                    await gv.admin_bot.set_group_ban(
                        group_id=gv.miao_group_num,
                        user_id=qqnum,
                        duration=60 * 60 * 24 * 29,
                    )
                    await group_notice.finish(
                        MessageSegment.at(qqnum)
                        + f"\n欢迎新人!\n来源: {come_from}\n联机教程和解除禁言方法都在群公告\n请认真阅读哦~ 不看退群"
                        + MessageSegment.image(f"{gv.site_url}/static/welcome.gif")
                    )

        ######## 审查群 ###########
        elif event.group_id == gv.shencha_group_num:
            await Shencha.delete_qqnum(qqnum)
            await group_notice.finish(
                MessageSegment.at(qqnum) + "如果有一小段连续的时间能在此群进行交流，请示意并配合审查组进行走流程"
            )

        ######## 其他 ###########
        elif event.group_id == gv.shencha_group_num:
            # 判断是否在黑名单
            if event.user_id in await Zhb_list.get_all_qq():
                nickname = await get_qqnum_nickname(qqnum)
                groupname = await get_group_name(event.group_id)
                gv.group_mess.append(
                    (
                        gv.shencha_group_num,
                        f"黑名单加群提醒！\n{nickname}({qqnum})\n加入了群\n{groupname}({event.group_id})\n黑名单链接: {gv.site_url}/why?qq={qqnum}",
                    )
                )


#####################################
# 管理员命令
#####################################
@test.handle()
@handle_exception("测试")
async def handle_test(event: MessageEvent):
    # await test.send("wc")
    results = []
    results_true = ["游戏中"]
    results_false = ["等待中"]
    for fangzhu in list(gv.rooms):
        # 读取房间信息
        room_data = gv.rooms[fangzhu][4]
        room_info = loads(
            bytes.fromhex(room_data[room_data.find("7b2273", 50) :]).decode()
        )
        chengyuan_info = ""
        # 获取成员信息
        for chengyuan in list(gv.rooms[fangzhu][0]):
            chengyuan_wgnum = int(ip_to_wgnum(chengyuan))
            # 特殊编号
            if chengyuan_wgnum in gv.r2f.keys():
                chengyuan_wgnum = gv.r2f[chengyuan_wgnum]
            # 特殊编号
            chengyuan_info += f"  {chengyuan_wgnum}"

        # 判断游戏状态
        if room_info["hsb"]:
            results_true.append(
                f"房主{ip_to_wgnum(fangzhu)} 人数{room_info['ccc']}\n成员{chengyuan_info}"
            )
        else:
            results_false.append(
                f"房主{ip_to_wgnum(fangzhu)} 人数{room_info['ccc']}\n成员{chengyuan_info}"
            )
    results = results_false + results_true
    await test.finish("\n".join(results))


@juesegaiming.handle()
@handle_exception("角色改名")
async def handle_juesegaiming(event: MessageEvent):
    in_mess = str(event.get_message())
    if in_mess == "角色改名":
        await juesegaiming.finish("角色改名 [旧名称] [新名称]")

    old_role_name, new_role_name = in_mess[4:].strip().split()
    host_role_get = False
    host_role_get_k = None
    for k, v in gv.host_role.items():
        if v == old_role_name:
            host_role_get = True
            host_role_get_k = k

    join_role_get = False
    join_role_get_k = None
    for k, v in gv.join_role.items():
        if v == old_role_name:
            join_role_get = True
            join_role_get_k = k

    if host_role_get and join_role_get:
        gv.host_role[host_role_get_k] = new_role_name
        gv.join_role[join_role_get_k] = new_role_name
        await gv.save_role_data()
        for k, v in gv.role_name.items():
            if v == old_role_name:
                gv.role_name[k] = new_role_name
        await juesegaiming.finish(f"角色{old_role_name}已重命名为{new_role_name}")

    elif host_role_get or join_role_get:
        await juesegaiming.finish(f"角色{old_role_name}数据未完整录入")
    else:
        await juesegaiming.finish(f"不存在角色{old_role_name}的数据")


@touxian.handle()
@handle_exception("头衔")
async def handle_touxian(event: MessageEvent):
    if gv.superuser_bot is not None:
        in_mess = str(event.get_message())[2:].strip()
        qqnum, title = in_mess.split()
        if await check_in_group(int(qqnum)):
            await gv.superuser_bot.set_group_special_title(
                group_id=gv.miao_group_num, user_id=int(qqnum), special_title=title
            )
            await touxian.finish("设置成功")
        else:
            await touxian.finish("目标不在群里")
    else:
        await touxian.finish("超级管理员bot未连接，设置失败")


@fasong.handle()
@handle_exception("发送")
async def handle_fasong(event: MessageEvent):
    in_mess = str(event.get_message())[2:].strip()
    await fasong.finish(in_mess)


@zhongyiying.handle()
@handle_exception("中译英")
async def handle_zhongyiying(event: MessageEvent):
    in_mess = str(event.get_message())[3:].strip()
    async with AsyncClient() as c:
        res = await c.get(
            "http://fanyi.youdao.com/translate?&doctype=json&type=ZH_CN2EN&i=" + in_mess
        )
    res_json = loads(res.text)
    out_mess = res_json["translateResult"][0][0]["tgt"]
    await zhongyiying.finish(out_mess)


@yingyizhong.handle()
@handle_exception("英译中")
async def handle_yingyizhong(event: MessageEvent):
    in_mess = str(event.get_message())[3:].strip()
    async with AsyncClient() as c:
        res = await c.get(
            "http://fanyi.youdao.com/translate?&doctype=json&type=EN2ZH_CN&i=" + in_mess
        )
    res_json = loads(res.text)
    out_mess = res_json["translateResult"][0][0]["tgt"]
    await yingyizhong.finish(out_mess)


@baipiao.handle()
@handle_exception("白嫖")
async def handle_baipiao(event: MessageEvent):
    if await Zhb_user.qq_exist(event.user_id):
        msg = str(event.get_message())
        if msg == "白嫖":
            await baipiao.finish(
                "QQ号列表如下\n"
                + "\n".join(await Nofree.get_all_qqnum())
                + "\n白嫖 [Q号]，删除在Q号前加“-”"
            )
        else:
            qqnum = msg[2:].strip()
            if qqnum[:1] == "-":
                if await Nofree.delete_qqnum(int(qqnum[1:])):
                    await baipiao.finish(f"删除{qqnum[1:]}成功")
                else:
                    await baipiao.finish(f"删除失败，目标不存在")
            else:
                qqnum = int(qqnum)
                if await Nofree.add_qqnum(qqnum):
                    if qqnum in gv.qq_verified.keys():
                        gv.qq_verified.pop(qqnum)
                    await baipiao.finish(f"增加{qqnum}成功")
                else:
                    await baipiao.finish(f"增加失败，目标已存在")


@sousuo.handle()
@handle_exception("搜索")
async def handle_sousuo(event: MessageEvent):
    await sousuo.send("搜索中，请稍后")
    qqnum = int(str(event.get_message())[2:].strip())
    # 结果输出
    out_mess = []
    # 获取群列表
    group_list = await gv.admin_bot.get_group_list(no_cache=True)
    # 遍历群
    for group in group_list:
        # 获取群成员信息
        group_member_data = await gv.admin_bot.get_group_member_list(
            group_id=group["group_id"], no_cache=True
        )

        # 遍历群成员检查是否在黑名单
        for user in group_member_data:
            if user["user_id"] == qqnum:
                out_mess.append(f'{group["group_name"]} ({group["group_id"]})\n')
                break

    if out_mess:
        await sousuo.finish("搜索结果\n\n" + "\n".join(out_mess))
    else:
        await sousuo.finish("搜索结果\n无")


@miaobixitong.handle()
@handle_exception("喵币系统")
async def handle_miaobixitong(event: MessageEvent):
    kw = str(event.get_message())[4:].strip()
    if kw == "打开":
        gv.miaobi_system = await Little_data.update_miaobi_system(1)
        await miaobixitong.finish("喵币系统打开")
    else:
        gv.miaobi_system = await Little_data.update_miaobi_system(0)
        await miaobixitong.finish("喵币系统关闭")


@anquanmoshi.handle()
@handle_exception("安全模式")
async def handle_anquanmoshi(event: MessageEvent):
    kw = str(event.get_message())[4:].strip()
    if kw == "打开":
        gv.safe_mode = await Little_data.update_safe_mode(1)
        await anquanmoshi.finish("安全模式打开")
    else:
        gv.safe_mode = await Little_data.update_safe_mode(0)
        await anquanmoshi.finish("安全模式关闭")


@weibangding.handle()
@handle_exception("未绑定")
async def handle_weibangding():
    wgnums = await Wg.get_all_unbind_wgnum()
    await weibangding.finish(f"未绑定的编号有{len(wgnums)}个如下:\n{str(wgnums)[1:-1]}")


@teshubianhao.handle()
@handle_exception("特殊编号")
async def handle_teshubianhao():
    out_mess = []
    for k, v in gv.f2r.items():
        out_mess.append(f"显示编号{k} >> 隐藏编号{v}")
    await teshubianhao.finish("\n".join(out_mess))


@feizanzhu.handle()
@handle_exception("非赞助")
async def handle_feizanzhu():
    wgnums = await Wg.get_all_unsponsor_wgnum()
    await feizanzhu.finish(f"非赞助编号有{len(wgnums)}个如下:\n{str(wgnums)[1:-1]}")


@bangding.handle()
@handle_exception("绑定")
async def handle_bangding(event: MessageEvent):
    if str(event.get_message())[-2:].strip() == "绑定":
        qqnum = str(event.get_message())[:-2].strip()
        wgnum = 0
    else:
        qqnum, wgnum = [int(x) for x in str(event.get_message())[:-2].strip().split()]

    # 判断是否在黑名单
    if qqnum in await Zhb_list.get_all_qq():
        await bangding.finish(f"{event.user_id}在黑名单中，禁止绑定")

    # 判断是否在群里
    if await check_in_group(qqnum):
        res = await bd_api(qqnum, wgnum)
        res = res.replace("<br />", "\n")
        await bangding.finish(res)

    else:
        await bangding.finish("人不在群里")


@jiebang.handle()
@handle_exception("解绑")
async def handle_jiebang(event: MessageEvent):
    num = str(event.get_message())[2:].strip()
    res = await jb_api(int(num))
    res = res.replace("<br />", "\n")
    await jiebang.finish(res)


@zanzhu.handle()
@handle_exception("赞助")
async def handle_zanzhu(event: MessageEvent):
    qqnum, money = str(event.get_message())[2:].strip().split()
    res = await zz_api(int(qqnum), money)
    res = res.replace("<br />", "\n")
    await zanzhu.finish(res)


@xiuluo.handle()
@handle_exception("修罗")
async def handle_xiuluo(event: MessageEvent):
    qqnum, xlnum = [int(x) for x in str(event.get_message())[2:].strip().split()]
    res = await xl_api(qqnum, xlnum)
    res = res.replace("<br />", "\n")
    await xiuluo.finish(res)


@kuorong.handle()
@handle_exception("扩容")
async def handle_kuorong(event: MessageEvent):
    num = str(event.get_message())[2:].strip()
    res = await krsr_api(int(num))
    res = res.replace("<br />", "\n")
    await kuorong.finish(res)


@chongzai.handle()
@handle_exception("重载")
async def handle_chongzai(event: MessageEvent):
    wgnum = int(str(event.get_message())[2:].strip())
    code, stdout, stderr = await exec_shell(
        f"bash src/shell/wg_renew.sh readd {wgnum_to_ip(wgnum)}"
    )
    if code:
        await chongzai.finish(f"{wgnum}号配置重载失败")
    else:
        await chongzai.finish(f"{wgnum}号配置重载成功")


@wangluo.handle()
@handle_exception("网络")
async def handle_wangluo():
    await wangluo.send("获取网络数据中，请稍后...")
    down_sum, up_sum = 0, 0
    down_max, up_max = 0, 0
    out_mess = ["序号  下载  上传 (KB/s)"]
    for i in range(10):
        download, upload = await get_net_io()
        down_sum += download
        if download > down_max:
            down_max = download
        if upload > up_max:
            up_max = upload
        up_sum += upload
        out_mess.append(f"<{i}>   {download}   {upload}")
    out_mess.append(
        f"联机人数: {gv.online}\n<A>   {round(down_sum/10)}   {round(up_sum/10)}\n<M>   {down_max}   {up_max}"
    )
    await wangluo.finish("\n".join(out_mess))


@zhuangtai.handle()
@handle_exception("状态")
async def handle_zhuangtai():
    res = await server_status()
    res = res.replace("<br />", "\n")
    await zhuangtai.finish(res)


@gonggaoliebiao.handle()
@handle_exception("公告列表")
async def handle_gonggaoliebiao():
    rows = await Tips.get_all_tip()
    await gonggaoliebiao.finish(
        "公告列表如下\n" + "\n".join([f"{row[0]} -- {row[1]}" for row in rows])
    )


@shanchugonggao.handle()
@handle_exception("删除公告")
async def handle_shanchugonggao(event: MessageEvent):
    id = int(str(event.get_message())[4:].strip())
    await Tips.delete_tip(id)
    await shanchugonggao.finish("删除成功")


@zengjiagonggao.handle()
@handle_exception("增加公告")
async def handle_zengjiagonggao(event: MessageEvent):
    tip = str(event.get_message())[str(event.get_message()).find("\n") + 1 :]
    id = await Tips.create_tip(tip)
    await zengjiagonggao.finish(f"增加成功,id={id}")


@zanzhuzonge.handle()
@handle_exception("赞助总额")
async def handle_zanzhuzonge():
    smoney = await Sponsor.get_money_sum()
    await zanzhuzonge.finish(f"当前赞助总金额: {smoney}")


@miaobizonge.handle()
@handle_exception("喵币总额")
async def handle_miaobizonge():
    smoney = await Gold.get_money_sum()
    await miaobizonge.finish(f"当前喵币总金额: {smoney}")


@miaobimochu.handle()
@handle_exception("喵币抹除")
async def handle_miaobimochu(event: MessageEvent):
    if str(event.get_message()) == "喵币抹除":
        await miaobimochu.finish("喵币抹除+Q号")
    else:
        qqnum = int(str(event.get_message())[4:].strip())
        if await Gold.delete_info(qqnum):
            await miaobimochu.finish(f"已抹除{qqnum}的喵币记录")
        else:
            await miaobimochu.finish(f"{qqnum}不存在喵币记录")


@shezhimiaobi.handle()
@handle_exception("设置喵币")
async def handle_shezhimiaobi(event: MessageEvent):
    if str(event.get_message()) == "设置喵币":
        await shezhimiaobi.finish("设置喵币 [Q号] [数额]")
    else:
        num, money = [int(x) for x in str(event.get_message())[4:].strip().split()]
        if await check_in_group(num):
            await Gold.set_money(num, money)
            await shezhimiaobi.finish(f"{num}的喵币设置为: {money}")
        else:
            await shezhimiaobi.finish("目标不在群里")


@zengjiamiaobi.handle()
@handle_exception("增加喵币")
async def handle_zengjiamiaobi(event: MessageEvent):
    if str(event.get_message()) == "增加喵币":
        await zengjiamiaobi.finish("增加喵币 [Q号] [数额]")
    else:
        num, money = [int(x) for x in str(event.get_message())[4:].strip().split()]
        if await check_in_group(num):
            await Gold.change_money(num, money, True)
            if isinstance(event, GroupMessageEvent):
                await zengjiamiaobi.finish(
                    MessageSegment.at(event.user_id) + f"{num}的喵币增加了: {money}"
                )
            elif isinstance(event, PrivateMessageEvent):
                await zengjiamiaobi.finish(f"{num}的喵币增加了: {money}")
        else:
            await zengjiamiaobi.finish("目标不在群里")


#####################################
# 审查组命令
#####################################
@pojieliuyan.handle()
@handle_exception("破解留言")
async def handle_pojieliuyan():
    await pojieliuyan.finish(
        f"经举报，发现你的游戏数据异常，需要进行核实是否存在破解/修改/第三方存档的情况，请加审查群{gv.shencha_group_num}，拒不配合将踢出群并上黑名单"
    )


@gaoxiuliuyan.handle()
@handle_exception("高修留言")
async def handle_gaoxiuliuyan():
    await gaoxiuliuyan.finish(
        f"经群友反馈你修罗较高，需要进行高修认证，请加审查群{gv.shencha_group_num}，拒不配合将踢出群"
    )


@liuchengtu.handle()
@handle_exception("流程图")
async def handle_liuchengtu():
    await liuchengtu.finish(MessageSegment.image(f"{gv.site_url}/static/shencha.jpg"))


@shencha.handle()
@handle_exception("审查")
async def handle_shencha(event: GroupMessageEvent):
    if await Zhb_user.qq_exist(event.user_id):
        if str(event.get_message()) == "审查":
            await shencha.finish("审查 [编号或Q号]")

        num = int(str(event.get_message())[2:].strip())
        qqnum = await Wg.get_qq_by_wgnum(num)
        if qqnum == 0:
            qqnum = num
        # 判断是否在群里
        if await check_in_group(qqnum):
            # 审查群通知大伙
            shencha_name = await Zhb_user.get_nick_by_qq(event.user_id)
            nickname = await get_qqnum_nickname(qqnum)
            wgnum = await Wg.get_wgnum_by_qq(qqnum)
            if wgnum == 0:
                wgnum = "无"

            await Shencha.add_qqnum(
                qqnum, f"{shencha_name} - {nickname} ({qqnum}) 编号 {wgnum}"
            )

            await gv.admin_bot.set_group_ban(
                group_id=gv.miao_group_num, user_id=qqnum, duration=60 * 60 * 24 * 7
            )
            await gv.admin_bot.send_group_msg(
                group_id=gv.shencha_group_num,
                message=f"{shencha_name}审查了{nickname} ({qqnum}) 编号 {wgnum}",
            )

        else:
            await shencha.finish("目标不在群内")


@jiejin.handle()
@handle_exception("解禁")
async def handle_jiejin(event: GroupMessageEvent):
    if await Zhb_user.qq_exist(event.user_id):
        num = int(str(event.get_message())[2:].strip())
        qqnum = await Wg.get_qq_by_wgnum(num)
        if qqnum == 0:
            qqnum = num
        # 判断是否在群里
        if await check_in_group(qqnum):
            await Shencha.delete_qqnum(qqnum)
            nickname = await get_qqnum_nickname(qqnum)
            await gv.admin_bot.set_group_ban(
                group_id=gv.miao_group_num, user_id=qqnum, duration=0
            )
            await jiejin.finish(f"已解禁{nickname} ({qqnum})")

        else:
            await jiejin.finish("目标不在群内")


@daishencha.handle()
@handle_exception("待审查")
async def handle_daishencha():
    shencha_list = await Shencha.get_all()
    await daishencha.finish("待审查列表" + "\n".join(shencha_list))


@tichu.handle()
@handle_exception("踢出")
async def handle_shencha(event: GroupMessageEvent):
    if await Zhb_user.qq_exist(event.user_id):
        if str(event.get_message()) == "踢出":
            await tichu.finish("踢出 [编号或Q号]\n踢出可改为永拒")

        if str(event.get_message())[:2] == "永拒":
            forever = True
        else:
            forever = False

        num = int(str(event.get_message())[2:].strip())
        qqnum = await Wg.get_qq_by_wgnum(num)
        if qqnum == 0:
            qqnum = num
        
        if qqnum in gv.qq_verified.keys():
            gv.qq_verified.pop(qqnum)

        # 判断是否在群里
        if await check_in_group(qqnum):
            # 从群里踢出
            await gv.admin_bot.set_group_kick(
                group_id=gv.miao_group_num, user_id=qqnum, reject_add_request=forever
            )
            await sleep(1)
            # 如果在二群顺便踢了
            try:
                await gv.admin_bot.set_group_kick(
                    group_id=gv.miao_group2_num, user_id=qqnum
                )
            except Exception:
                pass

            # 判断是否在审查列表
            if await Shencha.qqnum_exist(qqnum):
                gv.group_mess.append(
                    (
                        gv.shencha_group_num,
                        f"被审查目标踢出，该记录已移除\n{await Shencha.get_one(qqnum)}",
                    )
                )
                await Shencha.delete_qqnum(qqnum)
            # 解绑编号
            if await Wg.num_bind(qqnum):
                await release_wgnum(qqnum, True)

            nickname = await get_qqnum_nickname(qqnum)
            gv.group_mess.append(
                (
                    gv.miao_group_num,
                    f"{nickname}({qqnum})获得奖励"
                    + MessageSegment.image(f"{gv.site_url}/static/kick.jpg"),
                )
            )
            await tichu.finish(f"{nickname}({qqnum})已踢出")

        else:
            await tichu.finish("目标不在群内")


@chabang.handle()
@handle_exception("审查群查绑")
async def handle_chabang(event: GroupMessageEvent):
    if event.group_id != gv.shencha_group_num:
        await chabang.finish()
    elif str(event.get_message()) == "查绑":
        await chabang.finish("查绑+编号或Q号")
    else:
        num = int(str(event.get_message())[2:].strip())
        msg = await check_num(num)
        msg = sub("\(.*", "", msg)
        msg = msg.replace("<br />", "\n")
        await chabang.finish(msg)


@saomiao.handle()
@handle_exception("扫描")
async def handle_saomiao():
    await saomiao.send("扫描中，请稍后")
    out_mess = await check_group_zhb()
    await saomiao.finish(out_mess)


#####################################
# 喵服群聊命令
#####################################
@jinyan.handle()
@handle_exception("禁言")
async def handle_jinyan(event: GroupMessageEvent):
    if str(event.get_message()) == "禁言":
        await jinyan.finish("禁言 [Q号] （用于紧急禁言，严禁乱用）")
    qqnum = event.user_id
    ban_qqnum = int(str(event.get_message())[2:].strip())
    nickname = await get_qqnum_nickname(qqnum)

    # 恶意禁言
    if (
        ban_qqnum == qqnum
        or ban_qqnum == gv.superuser_num
        or ban_qqnum == int(gv.bot_1_num)
        or ban_qqnum == int(gv.bot_2_num)
    ):
        await gv.admin_bot.set_group_kick(group_id=gv.miao_group_num, user_id=qqnum)
        await sleep(1)
        if await Wg.num_bind(qqnum):
            await release_wgnum(qqnum, True)
        await Nofree.add_qqnum(qqnum)
        await sleep(1)
        await jinyan.finish(
            f"{nickname}({qqnum})获得奖励"
            + MessageSegment.image(f"{gv.site_url}/static/kick.jpg")
        )

    # 判断是否在群里
    if gv.jinyan_count > 2:
        await jinyan.finish("一小时内禁言次数超过3次，拒绝使用，如真的需要请联系服主")
    elif await check_in_group(ban_qqnum):
        gv.jinyan_count += 1
        ban_nickname = await get_qqnum_nickname(ban_qqnum)
        gv.private_mess.append(
            (
                gv.superuser_num,
                f"有人使用了临时禁言\n发起者 {nickname} ({qqnum})\n被禁者 {ban_nickname} ({ban_qqnum})",
            )
        )
        await gv.admin_bot.set_group_ban(
            group_id=gv.miao_group_num, user_id=ban_qqnum, duration=60 * 60 * 24 * 7
        )
        await jinyan.finish(f"已封禁{ban_nickname} ({ban_qqnum})，管理员看到会来处理，谢谢，若恶意封禁后果自负")

    else:
        await jinyan.finish("目标不在群内")


@yanzheng.handle()
@handle_exception("验证")
async def handle_yanzheng(event: GroupMessageEvent):
    if event.user_id in gv.qq_verified.keys():
        gv.qq_verified[event.user_id][1] = True


@link.handle()
@handle_exception("link")
async def handle_link(event: GroupMessageEvent):
    mess_dict = {
        "帮助": f"【支持的命令有以下】\n官网|教程|升级|排行\n后台|查房|频道|黑名单",
        "官网": f"喵服官网：{gv.site_url}",
        "教程": f"文字教程：{gv.site_url}/config\n视频教程：{gv.video_url}",
        "升级": f"升级编号：{gv.site_url}/get?x",
        "后台": f"玩家后台：{gv.site_url}/bk",
        "排行": f"排行榜：{gv.site_url}/xl",
        "赞助": f"赞助名单：{gv.site_url}/sponsor",
        "黑名单": f"黑名单：{gv.site_url}/zhb",
        "文章": f"文章列表：{gv.site_url}/guide",
        "频道": f"QQ频道：{gv.site_url}/channel",
        "群规": f"喵服群规&联机守则：{gv.site_url}/rule",
    }
    kw = str(event.get_message()).replace("\n", "")
    await link.finish(mess_dict[kw])


@chafang.handle()
@handle_exception("群查房")
async def handle_chafang(event: GroupMessageEvent):
    await chafang.finish(await get_room_list())


#####################################
# 私聊命令
#####################################
@pbangzhu.handle()
@handle_exception("私聊帮助")
async def handle_pbangzhu(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys() or event.user_id == gv.superuser_num:
        await pbangzhu.finish(
            "检测 -- 检测你是否连上服务器，接上编号可以测其他人的\n查绑 -- 查询绑定信息，接上编号可以查其他人的\n查房 -- 查看房间列表\n配置 -- 获取配置文件下载链接\n后台 -- 返回后台网页链接\n房名 房间名称 -- 自定义房间名称，取消直接发“房名”\n私有 目标编号 -- 只允许目标编号进入你的房间，多个编号用空格分开，取消直接发“私有”\n拉黑 目标编号 -- 禁止目标编号进入你的房间，多个编号用空格分开，取消直接发“拉黑”\n人数 人数上限 -- 设置你的房间人数上限，取消直接发“人数”\n版本 你游戏版本 -- 设置跨版本进房，比如你的版本是1.12.1，要进入其他版本的房间，就发送“版本 1.12.1”，取消直接发“版本”\n与网页设置同步，设置时不需要连着服务器"
        )


@pchafang.handle()
@handle_exception("私聊查房")
async def handle_pchafang(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys() or event.user_id == gv.superuser_num:
        await pchafang.finish(await get_room_list())


@plink.handle()
@handle_exception("私聊链接")
async def handle_plink(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys() or event.user_id == gv.superuser_num:
        mess_dict = {
            "官网": f"喵服官网(联机教程)：{gv.site_url}",
            "教程": f"文字教程：{gv.site_url}/config\n视频教程：{gv.video_url}",
            "后台": f"玩家后台：{gv.site_url}/bk",
            "排行": f"喵服修罗之力排行榜：{gv.site_url}/xl",
            "赞助": f"喵服赞助名单：{gv.site_url}/sponsor",
            "黑名单": f"黑名单：{gv.site_url}/zhb",
            "文章": f"文章列表：{gv.site_url}/guide",
            "领号": f"领号页面：{gv.site_url}/get",
            "升级": f"升级编号：{gv.site_url}/get?x",
        }
        kw = str(event.get_message()).replace("\n", "")
        await link.finish(mess_dict[kw])


@pchabang.handle()
@handle_exception("私聊查绑")
async def handle_pchabang(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys() or event.user_id == gv.superuser_num:
        if str(event.get_message()) == "查绑":
            await pchabang.finish("查绑+编号或Q号")
        else:
            num = int(str(event.get_message())[2:].strip())
            msg = await check_num(num)
            msg = msg.replace("<br />", "\n")
            await pchabang.finish(msg)


@pjiance.handle()
@handle_exception("私聊检测")
async def handle_pjiance(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys() or event.user_id == gv.superuser_num:
        if str(event.get_message()) == "检测":
            await pjiance.finish("检测+编号")
        else:
            wgnum = int(str(event.get_message())[2:].strip())
            msg = await network_status(wgnum, 1)
            if msg.find("ms") == -1:
                await pjiance.finish(msg)
            else:
                await pjiance.send(msg.replace("<br />", "\n"))
            msg = await network_status(wgnum, 2)
            await pjiance.finish(msg.replace("<br />", "\n"))


@pzhaokabi.handle()
@handle_exception("私聊找卡比")
async def handle_pjiance(event: PrivateMessageEvent):
    if str(event.get_message()) == "找卡比":
        await pzhaokabi.finish("找卡比+编号")
    else:
        wgnum = int(str(event.get_message())[3:].strip())
        await pzhaokabi.send("查询中，请稍后...")
        msg = await network_status(wgnum, 3)
        await pzhaokabi.finish(msg.replace("<br />", "\n"))


@peizhi.handle()
@handle_exception("私聊配置")
async def handle_peizhi(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys():
        link = gv.site_url + "/config?k=" + await Wg.get_key_by_wgnum(event.user_id)
        await peizhi.finish(f"配置文件下载链接，请复制链接到浏览器打开\n{link}")
    elif event.user_id == gv.superuser_num:
        wgnum = int(str(event.get_message())[2:].strip())
        # 特殊编号
        if wgnum in gv.f2r.keys():
            wgnum = gv.f2r[wgnum]
        else:
            wgnum = wgnum
        # 特殊编号
        if await Wg.num_bind(wgnum):
            link = gv.site_url + "/config?k=" + await Wg.get_key_by_wgnum(wgnum)
            await peizhi.finish(f"{wgnum}号的配置文件下载链接\n{link}")
        else:
            await peizhi.finish(f"{wgnum}号不存在")


@fangming.handle()
@handle_exception("私聊房名")
async def handle_fangming(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys():
        fm = str(event.get_message())[2:].strip()
        res = await room_name_api(fm, gv.friendlist[event.user_id])
        if res:
            await fangming.finish(res)
        else:
            await fangming.finish("无变更")


@siyou.handle()
@handle_exception("私聊私有")
async def handle_siyou(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys():
        sy = str(event.get_message())[2:].strip()
        res = await privacy_api(sy, gv.friendlist[event.user_id])
        if res:
            await siyou.finish(res)
        else:
            await siyou.finish("无变更")


@lahei.handle()
@handle_exception("私聊拉黑")
async def handle_lahei(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys():
        lh = str(event.get_message())[2:].strip()
        res = await black_api(lh, gv.friendlist[event.user_id])
        if res:
            await lahei.finish(res)
        else:
            await lahei.finish("无变更")


@renshu.handle()
@handle_exception("私聊人数")
async def handle_renshu(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys():
        rs = str(event.get_message())[2:].strip()
        res = await join_limit_api(rs, gv.friendlist[event.user_id])
        if res:
            await renshu.finish(res)
        else:
            await renshu.finish("无变更")


@banben.handle()
@handle_exception("私聊版本")
async def handle_banben(event: PrivateMessageEvent):
    if event.user_id in gv.friendlist.keys():
        bb = str(event.get_message())[2:].strip()
        res = await version_set_api(bb, gv.friendlist[event.user_id])
        if res:
            await banben.finish(res)
        else:
            await banben.finish("无变更")


#####################################
# 喵币相关命令
#####################################
@miaobi.handle()
@handle_exception("喵币")
async def handle_jinbi(event: GroupMessageEvent):
    money = await Gold.get_money(event.user_id)
    await miaobi.finish(MessageSegment.at(event.user_id) + f"你有{money}个喵币")


@miaobipaihang.handle()
@handle_exception("喵币排行")
async def handle_miaobipaihang():
    rows = await Gold.get_rank()
    out_mess = []
    count = 1
    index = {1: "壹", 2: "贰", 3: "叁", 4: "肆", 5: "伍", 6: "陆"}
    for row in rows:
        username = await get_qqnum_nickname(row[0])
        out_mess.append(f"{index[count]} > {username} > {row[1]}")
        count += 1

    out_mess = "\n".join(out_mess)
    await miaobipaihang.finish(out_mess)


@zhuanzhang.handle()
@handle_exception("转账")
async def handle_zhuanzhang(event: GroupMessageEvent):
    # 权限检查 管理员特权
    if event.user_id == gv.superuser_num:
        pass
    elif not await Sponsor.sponsor_exist(event.user_id):
        await zhuanzhang.finish(MessageSegment.at(event.user_id) + "该功能仅对喵服赞助者开放")

    if str(event.get_message()).strip() == "转账":
        await zhuanzhang.finish("转账 [Q号] [数额]")
    t, money = [int(x) for x in str(event.get_message())[2:].strip().split()]

    if not await check_in_group(t):
        await zhuanzhang.finish(MessageSegment.at(event.user_id) + "目标不存在")

    if money < 1000:
        await zhuanzhang.finish(MessageSegment.at(event.user_id) + "转账金额不能小于1k")

    code = await Gold.transfer(event.user_id, t, money)
    if code == 1:
        await zhuanzhang.finish(
            MessageSegment.at(event.user_id) + f"转了{money}个喵币给" + MessageSegment.at(t)
        )
    elif code == 0:
        await zhuanzhang.finish(MessageSegment.at(event.user_id) + "你钱呢？")


@qiandao.handle()
@handle_exception("签到")
async def handle_qiandao(event: GroupMessageEvent):
    sign_money = randint(30, 60)

    today = datetime.now()  # 获取当前时间
    today_str = today.strftime("%Y-%m-%d")  # datetime转str

    old_money, yesterday_str, con = await Gold.get_sign_info(event.user_id)
    yesterday = datetime.strptime(yesterday_str, "%Y-%m-%d")  # str转datetime

    if (today - yesterday).days == 0:
        msg = f"\n今天签到过啦，你已连续签到{con}天"

    elif (today - yesterday).days == 1:
        ext_money = int(sqrt(con)) * randint(3, 10)
        new_money = old_money + sign_money + ext_money
        await Gold.update_sign_info(event.user_id, new_money, today_str, con + 1)
        if randint(1, 100) == 1:
            ext_money *= 10
        msg = f"\n喵~ 连签{con + 1}天，获得{sign_money}个喵币\n额外获得{ext_money}个喵币"

    elif (today - yesterday).days == 2:
        await Gold.update_sign_info(event.user_id, old_money + sign_money, today_str, 0)
        msg = f"\n喵~ 获得{sign_money}个喵币\n你昨天断签啦！"

    else:
        await Gold.update_sign_info(event.user_id, old_money + sign_money, today_str, 0)
        msg = f"\n喵~ 获得{sign_money}个喵币"

    if gv.miaobi_system and gv.safe_mode is False:
        await qiandao.finish(MessageSegment.at(event.user_id) + msg)
    else:
        await qiandao.finish()


@fahongbao.handle()
@handle_exception("发红包")
async def handle_fahongbao(event: GroupMessageEvent):
    if str(event.get_message()) == "发红包":
        await fahongbao.finish("发红包+数额")

    if gv.packet_s > 0:
        await fahongbao.finish(
            MessageSegment.at(event.user_id)
            + f"{gv.packet_username_s}发的红包没抢完!还有{gv.packet_s}个喵币"
        )

    packet_num = int(str(event.get_message())[3:].strip())
    money = await Gold.get_money(event.user_id)

    if money >= packet_num:
        if packet_num >= 1000:
            # 检查当日发红包次数
            if await Gold.get_packet_count(event.user_id) >= 3:
                await fahongbao.finish(MessageSegment.at(event.user_id) + f"今天不让发了！")
            else:
                await Gold.update_packet_count(event.user_id)

            await Gold.change_money(event.user_id, packet_num, False)

            # 记录红包信息
            gv.packet_log_s = gv.packet_s = packet_num
            gv.packet_sender_qqnum = event.user_id
            if event.sender.card:
                gv.packet_username_s = event.sender.card
            else:
                gv.packet_username_s = event.sender.nickname

            gv.group_mess.append(
                (
                    gv.miao_group_num,
                    f"{gv.packet_username_s}发了喵币红包! 数量: {gv.packet_s}\n3分钟内发“抢喵币”瓜分红包",
                )
            )
            gv.group_mess.append(
                (
                    gv.miao_group2_num,
                    f"{gv.packet_username_s}发了喵币红包! 数量: {gv.packet_s}\n3分钟内发“抢喵币”瓜分红包",
                )
            )

            await sleep(180)
            if gv.packet_s > 0:
                await Gold.change_money(event.user_id, gv.packet_s, True)
                gv.group_mess.append(
                    (
                        gv.miao_group_num,
                        f"{gv.packet_username_s}的红包已过期，还有{gv.packet_s}个未瓜分，已返还",
                    )
                )
                gv.group_mess.append(
                    (
                        gv.miao_group2_num,
                        f"{gv.packet_username_s}的红包已过期，还有{gv.packet_s}个未瓜分，已返还",
                    )
                )
            gv.packet_s = 0
            gv.packet_once_s.clear()

        else:
            await fahongbao.finish(MessageSegment.at(event.user_id) + "这点钱还好意思发红包？")
    else:
        await fahongbao.finish(MessageSegment.at(event.user_id) + "钱都没有还发红包？")


@qiangmiaobi.handle()
@handle_exception("抢喵币")
async def handle_qiangmiaobi(event: GroupMessageEvent):
    grab = 0
    if gv.packet > 0 and event.user_id not in gv.packet_once:
        gv.packet_once.add(event.user_id)
        lucky = randint(1, 100)
        if lucky == 100:
            grab = randint(1, gv.packet)
            while grab > gv.packet_log / 4:
                grab = randint(1, gv.packet)
        else:
            grab = gv.packet
        gv.packet -= grab
        if gv.packet == 0:
            gv.group_mess.append((gv.miao_group_num, "随机红包被抢完了"))
            gv.group_mess.append((gv.miao_group2_num, "随机红包被抢完了"))

    grab_s = 0
    if gv.packet_s > 0 and event.user_id not in gv.packet_once_s:
        gv.packet_once_s.add(event.user_id)
        lucky = randint(1, 100)
        if lucky == 100:
            grab_s = randint(1, gv.packet_s)
            while grab_s > gv.packet_log_s / 4:
                grab_s = randint(1, gv.packet_s)
        else:
            grab_s = gv.packet_s
        gv.packet_s -= grab_s
        if gv.packet_s == 0:
            gv.group_mess.append((gv.miao_group_num, f"{gv.packet_username_s}的红包被抢完了"))
            gv.group_mess.append((gv.miao_group2_num, f"{gv.packet_username_s}的红包被抢完了"))

    grab_sum = grab + grab_s
    if grab_sum > 0:
        await Gold.change_money(event.user_id, grab_sum, True)
        await qiangmiaobi.finish(
            MessageSegment.at(event.user_id) + f"你抢到了{grab_sum}个喵币"
        )


@gailv.handle()
@handle_exception("概率")
async def handle_gailv(event: GroupMessageEvent):
    if event.group_id == gv.miao_group2_num:
        arr = [i for i in range(0, 100)]
        # 等于99为  1% 撸射
        l1 = l2 = l3 = l4 = l5 = l6 = 0
        for rand in arr:
            if rand == 99:
                l1 += 1
            # 等于0为  1% 清空
            elif rand == 0:
                l2 += 1
            # 魔法0-2倍  4%
            elif rand in [10, 30, 50, 70]:
                l3 += 1
            # 求余9为  12% 1-3倍
            elif rand % 8 == 0:
                l4 += 1
            # 求余3为  27% 1-2倍
            elif rand % 2 == 0:
                l5 += 1
            # 剩下扣  55%
            else:
                l6 += 1
        # print(l1, l2, l3, l4, l5, l6)
        # print(l1 + l2 + l3 + l4 + l5 + l6)
        await gailv.finish(
            f"撸射：{l1}%\n撸炸：{l2}%\nDuang：{l3}%\n0-3倍：{l4}%\n0-2倍：{l5}%\n爪子：{l6}%"
        )


@lumao.handle()
@handle_exception("撸猫")
async def handle_lumao(event: GroupMessageEvent):
    if event.group_id != gv.miao_group2_num:
        await lumao.finish(f"该命令只支持在二群使用，群号{gv.miao_group2_num}")

    # 查询用户余额
    money = await Gold.get_money(event.user_id)
    if money > 10:
        input = randint(1, money)
        rand = randint(0, 99)
        # 等于99为  1% 撸射
        if rand == 99:
            if money > 100:
                luck = randint(money * 4, money * 10)
            else:
                luck = randint(400, 1000)
            await Gold.set_money(event.user_id, luck)
            msg = f"撸射了！吞了所有喵币随后吐出{luck}个喵币"
        # 等于0为  1% 清空
        elif rand == 0:
            await Gold.set_money(event.user_id, 0)
            msg = f"撸炸了！吞了你{money}个喵币直接跑路"
        # 魔法0-2倍  4%
        elif rand in [10, 30, 50, 70]:
            await Gold.set_money(event.user_id, randint(0, money * 2))
            msg = "Duang！猜猜你的喵币有多少？"
        # 求余9为  12% 0-3倍
        elif rand % 8 == 0:
            get = randint(0, input * 3)
            await Gold.set_money(event.user_id, money + get)
            msg = f"吞了{input}个喵币，吐出{get+input}个喵币"
        # 求余3为  27% 0-2倍
        elif rand % 2 == 0:
            get = randint(0, input * 2)
            await Gold.set_money(event.user_id, money + get)
            msg = f"吞了{input}个喵币，吐出{get+input}个喵币"
        # 剩下扣  55%
        else:
            await Gold.set_money(event.user_id, money - input)
            msg = f"吞了{input}个喵币，并给你一爪子"

    elif money == 0:
        msg = "裤衩子都没了"
    else:
        msg = "留着裤衩子吧"

    await lumao.finish(MessageSegment.at(event.user_id) + msg)


@saolei_h.handle()
@handle_exception("扫雷帮助")
async def handle_saolei_h():
    tip = ""
    if gv.saolei_total != 0:
        tip = f"\n当前奖池: {int(gv.saolei_total * 0.8)}喵币"
    await saolei_h.finish(f"请从{gv.saolei_start}到{gv.saolei_end}之间选一个数字并发送 扫雷+数字{tip}")


@saoleikasi.handle()
@handle_exception("扫雷卡死")
async def handle_saoleikasi():
    gv.saolei_cd = False
    await saoleikasi.finish("ok")


@saolei.handle()
@handle_exception("扫雷")
async def handle_saolei(event: GroupMessageEvent):
    # 本局结束后等一会
    if gv.saolei_cd:
        await saolei.finish(MessageSegment.at(event.user_id) + "歇会")

    num = int(str(event.get_message())[2:].strip())

    # 判断数值范围
    if num not in range(gv.saolei_start + 1, gv.saolei_end):
        await saolei.finish(
            MessageSegment.at(event.user_id)
            + f"超出范围! ({gv.saolei_start}到{gv.saolei_end})"
        )

    # 不能重复扫
    if gv.saolei_once == event.user_id:
        await saolei.finish(MessageSegment.at(event.user_id) + "不能连续扫！")

    user = event.user_id

    # 查询用户余额
    money = await Gold.get_money(user)

    if money > 10:
        rand = randint(8, 16)

        # 扣币
        await Gold.change_money(user, rand, False)

        # 记录本次扫雷QQ号
        gv.saolei_once = event.user_id

        if gv.saolei_total == 0:
            gv.saolei_goal = randint(1, 99)
            await saolei.send("本局扫雷开始！")
            await sleep(0.5)
        gv.saolei_total += rand

        if num == gv.saolei_goal:
            gv.saolei_cd = True
            if gv.saolei_total == rand:
                try:
                    await saolei.send(
                        MessageSegment.at(event.user_id) + "\n一发命中！获得666喵币，本局扫雷结束!"
                    )
                except Exception:
                    pass
                await Gold.change_money(user, rand + 666, True)

            else:
                jiabei = randint(1, 100)
                tip = ""
                if jiabei > 99:
                    gv.saolei_total = gv.saolei_total * 10
                    tip = "触发十倍奖池！"
                elif jiabei > 90:
                    gv.saolei_total = gv.saolei_total * 3
                    tip = "触发三倍奖池！"
                elif jiabei > 70:
                    gv.saolei_total = gv.saolei_total * 2
                    tip = "触发双倍奖池！"
                try:
                    await saolei.send(
                        MessageSegment.at(event.user_id)
                        + f"\n恭喜{event.sender.nickname}猜中正确数字！{tip}获得{int(gv.saolei_total * 0.8)}喵币，本局扫雷结束!"
                    )
                except Exception:
                    pass
                await Gold.change_money(user, rand + int(gv.saolei_total * 0.8), True)
            await sleep(3)
            # 重置
            gv.saolei_cd = False
            gv.saolei_goal = 0
            gv.saolei_start = 0
            gv.saolei_end = 100
            gv.saolei_total = 0
            gv.saolei_once = 0
            await saolei.finish()

        else:
            if num > gv.saolei_goal:
                gv.saolei_end = num
            else:
                gv.saolei_start = num
            await saolei.finish(
                f"没猜中，吞了{rand}喵币\n下次范围{gv.saolei_start}到{gv.saolei_end}\n当前奖池: {int(gv.saolei_total * 0.8)}喵币"
            )
    else:
        await saolei.finish(MessageSegment.at(event.user_id) + "你喵币呢")
