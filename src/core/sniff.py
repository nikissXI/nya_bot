from asyncio import create_subprocess_exec, open_connection, subprocess, wait_for
from asyncio.exceptions import IncompleteReadError, TimeoutError
from datetime import datetime
from re import sub
from struct import pack
from time import time
from traceback import format_exc

from nonebot.log import logger
from src.models._little_data import Little_data
from src.models._wg import Wg
from ujson import loads

from .global_var import gv
from .utils import get_checksum, ip_to_wgnum, write_room_log


# 发送房间列表
def send_room_list(fangzhu_ip_list, finder_ip, dst_port):
    # 目标地址
    a, b, c, d = [int(x) for x in finder_ip.split(".")]
    dst_addr = [a, b, c, d]

    have_room = False
    # 遍历房间列表
    for i in fangzhu_ip_list:
        # 如果搜自己房间跳过
        if i == finder_ip or gv.rooms[i][4] == 0:
            continue
        # 游戏中房间不返回
        if gv.room_time[i][0]:
            continue
        # 如果私有房跳过
        if i in gv.privacy and finder_ip not in gv.privacy[i]:
            continue
        # 如果黑名单跳过
        if i in gv.black and finder_ip in gv.black[i]:
            continue

        have_room = True

        # 替换人数上限
        room_tmp = bytes.fromhex(gv.rooms[i][4])
        if i in list(gv.join_limit):
            room_tmp = sub(
                b'mcc":(.),',
                b'mcc":' + gv.join_limit[i].encode("utf-8") + b",",
                room_tmp,
                count=1,
                flags=0,
            )
        # 替换房间名
        if i in list(gv.room_name):
            # 自定义房名的
            room_tmp = sub(
                b'snn":"(.*)",',
                b'snn":"' + gv.room_name[i].encode("utf-8") + b'",',
                room_tmp,
                count=1,
                flags=0,
            )
        else:
            # 默认房名的
            # 特殊编号
            fangzhu_wgnum = ip_to_wgnum(i)
            if fangzhu_wgnum in gv.r2f.keys():
                fangzhu_wgnum = gv.r2f[fangzhu_wgnum]
            # 特殊编号
            room_tmp = sub(
                b'snn":"(.*)",',
                b'snn":"' + f"{fangzhu_wgnum}号的房间".encode("utf-8") + b'",',
                room_tmp,
                count=1,
                flags=0,
            )
        # 替换版本号
        if finder_ip in list(gv.version_set):
            room_tmp = sub(
                b'v":"(.*)"}',
                b'v":"' + gv.version_set[finder_ip].encode("utf-8") + b'"}',
                room_tmp,
                count=1,
                flags=0,
            )
        # 重新计算房间json字符串长度
        room_tmp = sub(
            b'.{2}{"s',
            pack("!B", len(room_tmp) - room_tmp.find(b'\x00{"s', 30)) + b'\x00{"s',
            room_tmp,
            count=1,
            flags=0,
        )
        # 发送数据包
        udp_len = 8 + len(room_tmp)
        # 源地址
        a, b, c, d = [int(x) for x in i.split(".")]
        src_addr = [a, b, c, d]
        gv.send_socket.send(
            # 由于大部分数据都可以固定的，所以直接用数字
            pack(
                "!BBHHHBBH4B4B",
                69,  # 头部长度和版本
                0,  # 服务
                20 + udp_len,  # 数据包总长度
                8888,  # 标识
                16384,  # flags和offset
                64,  # ttl
                17,  # 协议
                get_checksum(
                    pack(
                        "!BBHHHBBH4B4B",
                        69,  # 头部长度和版本
                        0,  # 服务
                        20 + udp_len,  # 数据包总长度
                        8888,  # 标识
                        16384,  # flags和offset
                        64,  # ttl
                        17,  # 协议
                        0,  # 校验和
                        *src_addr,  # 源IP
                        *dst_addr,  # 目的IP
                    )
                ),
                *src_addr,  # 源IP
                *dst_addr,  # 目的IP
            )
            + pack("!HHHH", 46797, dst_port, udp_len, 0)  # 源端口  # 目的端口  # UDP长度  # 校验和
            + room_tmp  # 数据
        )

    if have_room is False:
        text = {
            "1": "现在没有可加入的房间",
            "2": "开房就直接点创建房间",
        }
        for k, v in text.items():
            # 源地址
            src_addr = [a, b, 255, 1]

            notice_room = (
                b"\xc4 \xb7\xe6|=%+\x17\x00tcp4://localhost:6797/\xb5\xf1\xf5\x05"
                + k.encode()
                + b'\xff\xd8\xa9?\x00{"snn":"'
                + v.encode()
                + b'","mcc":1,"ccc":1,"hsb":true,"v":"1.12.7"}'
            )
            # 重新计算房间json字符串长度
            notice_room = sub(
                b'.{2}{"s',
                pack("!B", len(notice_room) - notice_room.find(b'\x00{"s', 30))
                + b'\x00{"s',
                notice_room,
                count=1,
                flags=0,
            )
            # 发送数据包
            udp_len = 8 + len(notice_room)
            gv.send_socket.send(
                # 由于大部分数据都可以固定的，所以直接用数字
                pack(
                    "!BBHHHBBH4B4B",
                    69,  # 头部长度和版本
                    0,  # 服务
                    20 + udp_len,  # 数据包总长度
                    8888,  # 标识
                    16384,  # flags和offset
                    64,  # ttl
                    17,  # 协议
                    get_checksum(
                        pack(
                            "!BBHHHBBH4B4B",
                            69,  # 头部长度和版本
                            0,  # 服务
                            20 + udp_len,  # 数据包总长度
                            8888,  # 标识
                            16384,  # flags和offset
                            64,  # ttl
                            17,  # 协议
                            0,  # 校验和
                            *src_addr,  # 源IP
                            *dst_addr,  # 目的IP
                        )
                    ),
                    *src_addr,  # 源IP
                    *dst_addr,  # 目的IP
                )
                + pack(
                    "!HHHH", 46797, dst_port, udp_len, 0
                )  # 源端口  # 目的端口  # UDP长度  # 校验和
                + notice_room  # 数据
            )


# 创建房间
async def room_create(fangzhu, room_data):
    # 模拟加入房间，获取房主数据
    pos = -1
    try:
        fun_connect = open_connection(fangzhu, 6797)
        reader, writer = await wait_for(fun_connect, timeout=1)
        writer.write(
            b"\x00\x00\x00\x0e\x7e\xe0\x2a\x4f\x20\xec\x64\x3f\x3c\x9d\x1d\x33\x90\xdd"
        )
        await writer.drain()
    except (TimeoutError, ConnectionRefusedError):
        pass
    except Exception as e:  # (ConnectionResetError)
        gv.private_mess.append(
            (gv.superuser_num, f"获取{fangzhu}房主角色时握手出错，错误: {repr(e)}")
        )
    else:
        try:
            fun_readdata = reader.readuntil(b"\x80\x00\x00\x00\x80")
            host_data = await wait_for(fun_readdata, timeout=1)
            # 获取角色信息的相对位置
            pos = host_data.find(b"\x64\x40\x02\x00\x00")
        except (TimeoutError, IncompleteReadError):
            pass
        except Exception as e:
            gv.private_mess.append(
                (gv.superuser_num, f"获取{fangzhu}房主角色时读取出错，错误: {repr(e)}")
            )
        finally:
            writer.write_eof()
            writer.close()
            fun_close = writer.wait_closed()
            await wait_for(fun_close, timeout=1)

    # 识别房主角色
    if pos != -1:
        # 判断人物
        if fangzhu in gv.role_name:
            last_role = gv.role_name[fangzhu]
        try:
            gv.role_name[fangzhu] = gv.host_role[host_data[pos + 16 : pos + 24]]
        except Exception:
            gv.role_name[fangzhu] = "未知"
            gv.host_role[host_data[pos + 16 : pos + 24]] = "未知"
            join_role_get = False
            for k, v in gv.join_role.items():
                if v == "未知":
                    join_role_get = True
            if join_role_get:
                msg = f"已完整录入未知角色数据，请发送指令“角色改名”为该角色命名"
            else:
                msg = f"发现未知房主角色数据，等待加入角色数据录入"
            logger.error(msg)
            gv.private_mess.append((gv.superuser_num, msg))

        # 存储房间信息
        gv.rooms[fangzhu] = [{}, [], 0, 3, room_data]
        # 房间创建提醒
        if fangzhu not in gv.room_time or (
            fangzhu in gv.room_time
            and (
                last_role != gv.role_name[fangzhu]
                or int(time()) - gv.room_time[fangzhu][1] > 60
            )
        ):
            gv.room_time[fangzhu] = [0, int(time())]
            if fangzhu in list(gv.privacy):
                prim = "   [私有]"
            else:
                prim = ""
            fangzhu_wgnum = int(ip_to_wgnum(fangzhu))
            # 特殊编号
            if fangzhu_wgnum in gv.r2f.keys():
                fangzhu_wgnum = gv.r2f[fangzhu_wgnum]
            # 特殊编号
            now = datetime.now()
            # 获取房名
            if fangzhu in list(gv.room_name):
                if len(gv.room_name[fangzhu]) > 12:
                    room_name = gv.room_name[fangzhu][:10] + "..."
                else:
                    room_name = gv.room_name[fangzhu]
            else:
                room_name = f"{fangzhu_wgnum}号的房间"
            msg = f"◤{now.hour:02d}:{now.minute:02d}:{now.second:02d}◢{prim}\n{fangzhu_wgnum}号用[{gv.role_name[fangzhu]}]创建了房间\n▶ {room_name}"
            gv.group_mess.append((gv.miao_group_num, msg))
            gv.channel_mess.append((gv.channel_id, msg))
            # 创建房间信息
            await write_room_log(fangzhu_wgnum, "", gv.role_name[fangzhu], True)


# 玩家加入房间
async def room_join(data, fangzhu, chengyuan):
    # 判断人物
    try:
        gv.role_name[chengyuan] = gv.join_role[data]
    except Exception:
        gv.role_name[chengyuan] = "未知"
        gv.join_role[data] = "未知"
        host_role_get = False
        for k, v in gv.host_role.items():
            if v == "未知":
                host_role_get = True
        if host_role_get:
            msg = f"已完整录入未知角色数据，请发送指令“角色改名”为该角色命名"
        else:
            msg = f"发现未知加入角色数据，等待房主角色数据录入"
        logger.error(msg)
        gv.private_mess.append((gv.superuser_num, msg))

    chengyuan_wgnum = int(ip_to_wgnum(chengyuan))
    fangzhu_wgnum = int(ip_to_wgnum(fangzhu))
    # 特殊编号
    if chengyuan_wgnum in gv.r2f.keys():
        chengyuan_wgnum = gv.r2f[chengyuan_wgnum]
    if fangzhu_wgnum in gv.r2f.keys():
        fangzhu_wgnum = gv.r2f[fangzhu_wgnum]
    # 特殊编号

    await write_room_log(chengyuan_wgnum, fangzhu_wgnum, gv.role_name[chengyuan])

    if (
        fangzhu in gv.vip_ip.keys()
        and fangzhu in gv.rooms.keys()
        and chengyuan not in gv.rooms[fangzhu][1]
    ):
        gv.rooms[fangzhu][1].append(chengyuan)
        now = datetime.now()
        gv.private_mess.append(
            (
                gv.vip_ip[fangzhu],
                f"◤{now.hour:02d}:{now.minute:02d}:{now.second:02d}◢\n{chengyuan_wgnum}号用[{gv.role_name[chengyuan]}]加入了你的房间",
            )
        )


# 房间开始游戏
async def room_start(fangzhu):
    # 记录开始时间
    gv.room_time[fangzhu] = [int(time()), 0]
    for chengyuan in list(gv.rooms[fangzhu][0]):
        await Wg.update_play_flag_by_wgnum(int(ip_to_wgnum(chengyuan)))
        await Little_data.update_play_count_today()
    await Wg.update_play_flag_by_wgnum(int(ip_to_wgnum(fangzhu)))
    # 增加联机人次
    await Little_data.update_play_count_today()


# 数据包回调函数
async def packet_called(p):
    try:
        # TCP报文
        if p["ip_proto"][0] == "6":
            # 房间状态半连接扫描
            if p["tcp_dstport"][0] == str(gv.room_scan_port):
                fangzhu = p["ip_src"][0]
                if fangzhu in list(gv.rooms):
                    # 如果reset，说明房间关闭
                    if p["tcp_flags_reset"][0] == "1":
                        gv.rooms.pop(fangzhu)
                return

            # 玩家进房和连接状态
            # 如果目标地址不是房主IP直接pass
            if p["ip_dst"][0] not in list(gv.rooms):
                return

            fangzhu = p["ip_dst"][0]
            chengyuan = p["ip_src"][0]
            # 玩家加入房间通知，等待中的房间才进行处理
            if (
                gv.room_time[fangzhu][0] == 0
                and p["ip_len"][0] != "52"
                and p["ip_len"][0] != "40"
                and "data" in p.keys()
            ):
                await room_join(p["data"][0][24:38], fangzhu, chengyuan)

            # 房间成员连接情况
            if fangzhu in list(gv.rooms):
                gv.rooms[fangzhu][0][chengyuan] = 1

        # UDP报文
        # elif p["ip_proto"][0] == "17":
        else:
            # 接收房间信息
            if p["ip_dst"][0] == gv.wireguard_gateway:
                fangzhu = p["ip_src"][0]
                # 在房间列表
                if fangzhu in gv.rooms:
                    # 更新房间数据
                    gv.rooms[fangzhu][4] = p["data"][0]
                    gv.rooms[fangzhu][3] = 3
                    # 是否为等待状态
                    if p["data"][0].find("66616c7365", 120) != -1:
                        # 之前是否为游戏中，游戏中变等待，重置房间数据
                        if gv.room_time[fangzhu][0]:
                            gv.room_time[fangzhu][0] = 0
                            gv.rooms.pop(fangzhu)
                    # 游戏状态
                    else:
                        # 之前是否为等待中，等待变游戏中就是开始游戏
                        if gv.room_time[fangzhu][0] == 0:
                            await room_start(fangzhu)
                # 不在房间列表
                else:
                    # 是否为等待状态，是就创建新房间
                    if p["data"][0].find("66616c7365", 120) != -1:
                        await room_create(fangzhu, p["data"][0])
                    # 未响应后恢复，直接把数据补回去
                    else:
                        gv.rooms[fangzhu] = [{}, [], 0, 3, p["data"][0]]

            # 返回房间列表信息给搜房者
            else:
                finder_ip = p["ip_src"][0]
                src_port = p["udp_srcport"][0]
                # 判断是否发送过房间列表
                if finder_ip in gv.forward_once.keys():
                    # 如果端口号一样代表发送过，就不处理
                    if gv.forward_once[finder_ip] == src_port:
                        return
                # 没发送过就记录本次来源的IP和端口号
                else:
                    gv.forward_once[finder_ip] = src_port
                # 返回房间列表
                send_room_list(list(gv.rooms), finder_ip, int(src_port))
    except Exception:
        error_msg = f"数据包回调函数出错!\n错误追踪:\n{format_exc()}\n数据包:{p}"
        logger.error(error_msg)
        gv.private_mess.append((gv.superuser_num, error_msg))


async def read_stdout(proc: subprocess.Process):
    try:
        # 抓够次数就结束子进程，释放内存
        while gv.p_count < 500000:
            buf = await proc.stdout.readuntil(separator=b"\n")
            # 跳过分隔符
            if buf[:3] == b'{"i':
                continue
            else:
                # 数据包计数
                gv.p_count += 1
                # 解析json格式数据包
                p = loads(buf.decode())
                # 执行数据包回调
                await packet_called(p["layers"])

        # 重置次数，结束子进程
        if gv.p_count == 1000000:
            gv.p_count = -1
        else:
            gv.p_count = 0
        proc.terminate()
    except IncompleteReadError:
        pass
    except Exception:
        error_msg = f"tshark数据解析函数出错!\n错误追踪:\n{format_exc()}"
        logger.error(error_msg)
        gv.private_mess.append((gv.superuser_num, error_msg))


async def start_sniff():
    # 创建子进程
    logger.success("流量嗅探模块加载成功")
    while gv.p_count != -1:
        proc = await create_subprocess_exec(
            *[
                gv.tshark_path,
                "-i",
                "miao",
                "-l",
                "-n",
                "-T",
                "fields",
                "-e",
                "ip.len",
                "-e",
                "ip.proto",
                "-e",
                "ip.src",
                "-e",
                "ip.dst",
                "-e",
                "tcp.dstport",
                "-e",
                "udp.srcport",
                "-e",
                "tcp.flags.reset",
                "-e",
                "data",
                "-T",
                "ek",
                "-f",
                f"\
                (ip dst {gv.wireguard_gateway} and udp dst port {gv.room_scan_port} and udp src port 46797) or \
                (ip dst {gv.wireguard_sub_gateway}.255.255 and udp dst port 46797) or \
                ((ip[8] == 64 or ip[8] == 128) and tcp[tcpflags] & tcp-push != 0 and tcp dst port 6797 and (tcp[44:2] == 0x2d1e or tcp[32:2] == 0x2d1e)) or \
                ((ip[8] == 64 or ip[8] == 128) and tcp[tcpflags] & tcp-push == 0 and tcp dst port 6797 and (ip[2:2] == 52 or ip[2:2] == 40) and ip src not {gv.wireguard_gateway}) or \
                (ip dst {gv.wireguard_gateway} and tcp dst port {gv.room_scan_port})",
                # 1、捕获返回给服务器的房间信息数据包
                # 2、捕获玩家搜房的广播包
                # 3、捕获玩家的加房数据包
                # 4、捕获玩家通信状态
                # 5、捕获SYN半连接扫描返回的RESET包，检测房间是否关闭
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # 从管道读取内容
        await read_stdout(proc)

    logger.success("流量嗅探已停止")
