from asyncio import create_subprocess_shell, gather, subprocess
from datetime import datetime
from functools import wraps
from re import search
from struct import unpack
from traceback import format_exc

from nonebot import get_bots
from nonebot.adapters.onebot.v11 import ActionFailed, NetworkError
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.exception import FinishedException
from nonebot.log import logger
from psutil import cpu_percent, virtual_memory
from src.models._little_data import Little_data
from src.models._zhb_list import Zhb_list

from .global_var import gv


###################################
# 异常处理
###################################
def handle_exception(name: str, channel: bool = False):
    def wrapper(func):
        @wraps(func)
        async def inner(**kwargs):
            try:
                await func(**kwargs)
            except ActionFailed:
                if channel:
                    # 此为bot本身由于风控或网络问题发不出消息，并非代码本身出问题
                    error_msg = f"{name} 处理器消息发送失败"
                    logger.error(error_msg)
                    await gv.admin_bot.send_private_msg(
                        user_id=gv.superuser_num, message=error_msg
                    )
                else:
                    gv.miaobi_system = False
                    gv.safe_mode = True
                    # 此为bot本身由于风控或网络问题发不出消息，并非代码本身出问题
                    error_msg = f"{name} 处理器消息发送失败，已临时关闭喵币系统并开启安全模式"
                    logger.error(error_msg)
                    await gv.admin_bot.send_private_msg(
                        user_id=gv.superuser_num,
                        message=error_msg,
                    )
            except NetworkError:
                pass
                # error_msg = f"{name} 处理器执行出错!\napi响应超时"
                # logger.error(error_msg)
                # await gv.admin_bot.send_private_msg(
                #     user_id=gv.superuser_num,
                #     message=error_msg,
                # )
            except FinishedException:
                # `finish` 会抛出此异常，应予以抛出而不处理
                raise
            except Exception:
                # 代码本身出问题
                error_msg = f"{name} 处理器执行出错!\n错误追踪:\n{format_exc()}"
                logger.error(error_msg)
                await gv.admin_bot.send_private_msg(
                    user_id=gv.superuser_num,
                    message=error_msg,
                )

        return inner

    return wrapper


###################################
# 数据处理接口
###################################

# 获取QQ昵称
async def get_qqnum_nickname(qqnum: int) -> str:
    user_data = await gv.admin_bot.get_stranger_info(user_id=qqnum, no_cache=True)
    return user_data["nickname"]


# 获取QQ群名称
async def get_group_name(groupnum: int) -> str:
    group_data = await gv.admin_bot.get_group_info(group_id=groupnum, no_cache=True)
    return group_data["group_name"]


# 检查群内黑名单
async def check_group_zhb() -> str:
    # 结果输出
    out_mess = []
    # 获取黑名单列表
    zhb_list = await Zhb_list.get_all_qq()
    # 获取群列表
    group_list = await gv.admin_bot.get_group_list(no_cache=True)
    # 遍历群
    for group in group_list:
        # 获取群成员信息
        group_member_data = await gv.admin_bot.get_group_member_list(
            group_id=group["group_id"], no_cache=True
        )
        qq_list = []
        # 遍历群成员检查是否在黑名单
        for user in group_member_data:
            if user["user_id"] in zhb_list:
                nickname = await get_qqnum_nickname(user["user_id"])
                # 记录qq所在群消息和昵称
                qq_list.append(
                    f"{nickname} ({user['user_id']})\n{gv.site_url}/why?qq={user['user_id']}"
                )

        if qq_list:
            out_mess += (
                [f'{group["group_name"]} ({group["group_id"]})\n===分割线===']
                + qq_list
                + ["\n"]
            )

    if out_mess:
        return "黑名单扫描结果\n\n" + "\n".join(out_mess)
    else:
        return "黑名单扫描结果\n空"


# 执行异步shell子进程
async def exec_shell(shell: str) -> tuple[int, bytes, bytes]:
    proc = await create_subprocess_shell(
        shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stderr:
        error_msg = (
            f"shell子进程执行有错误信息（也可能是警告）\n被执行的命令: {shell}\n错误信息:\n{stderr.decode()}"
        )
        logger.error(error_msg)
        gv.private_mess.append((gv.superuser_num, error_msg))
    return (proc.returncode, stdout, stderr)


# 判断是否在群里
async def check_in_group(qqnum: int) -> bool:
    if gv.admin_bot is not None:
        try:
            await gv.admin_bot.get_group_member_info(
                group_id=gv.miao_group_num, user_id=qqnum, no_cache=True
            )
            res = True
        except Exception:
            res = False
    else:
        res = False
    return res


# 设置群名片
async def set_group_card(qqnum: int, wgnum: str = ""):
    if gv.admin_bot is not None and qqnum != gv.superuser_num:
        try:
            await gv.admin_bot.set_group_card(
                group_id=gv.miao_group_num, user_id=qqnum, card=str(wgnum)
            )
        except Exception:
            pass


# 校验和计算
def get_checksum(data: bytes) -> int:
    sum = 0
    data = unpack(f"!{int(len(data)/4)}I", data)
    for i in data:
        sum = sum + i
        sum = (sum >> 16) + (sum & 0xFFFF)
    sum = (sum >> 16) + (sum & 0xFFFF)
    return ~sum & 0xFFFF


def wgnum_to_ip(wgnum: int) -> str:
    a = wgnum // 255
    b = wgnum % 255
    if b == 0:
        a -= 1
        b = 255
    return f"{gv.wireguard_sub_gateway}.{a}.{b}"


def ip_to_wgnum(ip: str) -> str:
    a, b, c, d = ip.split(".")
    return f"{255 * int(c) + int(d)}"


async def write_room_log(player: str, fangzhu: str, role: str, hoster: bool = False):
    now = datetime.now()
    if hoster:
        text = f"{now.hour}:{now.minute:02d}:{now.second:02d} {player}号使用{role}创建房间"
    else:
        text = f"{now.hour}:{now.minute:02d}:{now.second:02d} {player}号使用{role}加入{fangzhu}号房间"
    await exec_shell(
        f"echo {text} >> log/room_log/{now.year}-{now.month}-{now.day}.txt"
    )


async def write_bd_log(qqnum: int, wgnum: int):
    now = datetime.now()
    text = f"{now.month}-{now.day} {now.hour}:{now.minute:02d} {qqnum} 绑定{wgnum}号"
    await exec_shell(f"echo {text} >> log/bd_log/{now.year}-{now.month}.txt")


async def write_ip_log(qqnum: int, ip: str):
    now = datetime.now()
    text = f"{now.month}-{now.day} {now.hour}:{now.minute:02d} {qqnum} 使用{ip}访问"
    await exec_shell(f"echo {text} >> log/ip_log/{now.year}-{now.month}.txt")


async def ping(ip: str, count: int) -> tuple[int, list]:
    code, stdout, stderr = await exec_shell(f"ping {ip} -c {count} -W 1 -q")
    if code:
        return 1, []
    else:
        res = stdout.decode()
        data = search(r"= (.*) ms", res).group(1)
        lost = search(r"received, (.*)%", res).group(1)
        data = data.split("/")
        # 状态码、最低、平均、最大、丢包率
        return (
            0,
            [
                round(float(data[0])),
                round(float(data[1])),
                round(float(data[2])),
                round(float(lost)),
            ],
        )


async def network_status(wgnum: int, op_type: int) -> str:
    # 特殊编号
    if wgnum in gv.f2r.keys():
        wgnum = gv.f2r[wgnum]
    # 特殊编号

    ip_addr = wgnum_to_ip(wgnum)

    # 特殊编号
    if wgnum in gv.r2f.keys():
        wgnum = gv.r2f[wgnum]
    # 特殊编号

    # 瞬时检测
    if op_type == 1:
        code, data = await ping(ip_addr, 1)

        if code:
            return f"{wgnum}号未连接或不能被检测"
        else:
            return f"{wgnum}号已连接,瞬时延迟{data[1]}ms<br />10秒后返回详细数据"

    # 长时检测
    elif op_type == 2:
        code, data = await ping(ip_addr, 10)
        return f"{wgnum}号详细延迟数据<br />平均{data[1]},最高{data[2]},丢包{data[3]}%"

    # 找卡比
    else:
        if ip_addr not in gv.rooms:
            return f"{wgnum}号没开房呢"

        else:
            members = []
            members.append(ip_addr)
            for member_ip in gv.rooms[ip_addr][0]:
                members.append(member_ip)
            out_mess = [f"{wgnum}号房延迟数据如下"]

            async def _kabi(ip):
                code, data = await ping(ip, 10)
                wgnum = int(ip_to_wgnum(ip))
                # 特殊编号
                if wgnum in gv.r2f.keys():
                    wgnum = gv.r2f[wgnum]
                # 特殊编号
                if code:
                    out_mess.append(f"{wgnum}: 无法检测")
                else:
                    out_mess.append(f"{wgnum}: 平均{data[1]},最高{data[2]},丢包{data[3]}%")

            task = [_kabi(ip) for ip in members]
            await gather(*task)
            return "<br />".join(out_mess)


async def get_wg_content(ip: str) -> str:
    code, stdout, stderr = await exec_shell(f"cat tunnel/conf/{ip}.conf")
    return stdout.decode()


async def get_net_io() -> tuple[int, int]:
    code, stdout, stderr = await exec_shell(f"bash src/shell/speed.sh {gv.interface_name}")
    download, upload = stdout.decode().split(" ")
    return (round(float(download)), round(float(upload)))


async def server_status() -> str:
    out_mess = []
    # 获取运行时间
    now = datetime.now()
    run_time = now - gv.start_time
    out_mess.append(
        f"已运行{str(run_time).replace(' day, ', '天').replace(' days, ', '天').split('.')[0].replace(':', '时', 1).replace(':', '分', 1)+ '秒'}"
    )
    # 获取CPU和RAM使用率
    out_mess.append(
        f"CPU: {int(cpu_percent(interval=1))}%   RAM: {int(virtual_memory().percent)}%"
    )
    download, upload = await get_net_io()
    out_mess.append(f"▼: {download}KB/秒  ▲: {upload}KB/秒")
    out_mess.append(f"联机人数: {gv.online}")
    out_mess.append(f"喵币系统: {gv.miaobi_system}")
    out_mess.append(f"安全模式: {gv.safe_mode}")
    out_mess.append(f"机器人在线列表")
    bots = get_bots()
    for bot_id in bots.keys():
        nickname = await get_qqnum_nickname(int(bot_id))
        out_mess.append(f"{nickname} >> {bot_id}")
    return "<br />".join(out_mess)


async def get_room_list() -> str:
    play_count_yestoday = await Little_data.get_play_count_yestoday()
    play_count_today = await Little_data.get_play_count_today()
    if gv.online:
        return (
            f"今日联机{play_count_today}人次(昨天{play_count_yestoday})"
            + MessageSegment.image(f"{gv.site_url}/static/roomlist.gif")
        )
    else:
        return (
            f"今日联机{play_count_today}人次(昨天{play_count_yestoday})\n你来开个房间？"
            + MessageSegment.image(f"{gv.site_url}/static/wait.gif")
        )
