from asyncio import sleep, get_running_loop
from copy import deepcopy
from datetime import datetime, timedelta
from random import choice, randint
from struct import pack
from time import time
from traceback import format_exc

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from nonebot.log import logger
from PIL import Image, ImageDraw, ImageFont
from src.models._gold import Gold
from src.models._little_data import Little_data
from src.models._shencha import Shencha
from src.models._sponsor import Sponsor
from src.models._tips import Tips
from src.models._visit import Visit
from src.models._wg import Wg
from ujson import loads

from .global_var import gv
from .utils import check_group_zhb, check_in_group, get_checksum, ip_to_wgnum
from .wgnum import refresh_friendlist, release_wgnum

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


# 启动
async def start_scheduler():
    scheduler.start()
    logger.success("定时任务模块加载成功")


# 消息发送
@scheduler.scheduled_job("interval", seconds=1)
async def send_game_message():
    # 私聊信息
    if gv.admin_bot is not None and gv.private_mess:
        tmp = deepcopy(gv.private_mess)
        gv.private_mess.clear()

        for mess in tmp:
            try:
                await gv.admin_bot.send_private_msg(user_id=mess[0], message=mess[1])
            except Exception:
                error_msg = f"私聊信息数组发送失败，消息内容如下\n\n{mess[1]}"
                logger.error(error_msg)
                await gv.admin_bot.send_private_msg(
                    user_id=gv.superuser_num,
                    message=error_msg,
                )
                break
    else:
        gv.private_mess.clear()

    # 频道消息
    if gv.handle_bot is not None and gv.channel_mess:
        tmp = deepcopy(gv.channel_mess)
        gv.channel_mess.clear()
        for mess in tmp:
            try:
                await gv.handle_bot.send_guild_channel_msg(
                    guild_id=gv.guild_id, channel_id=gv.channel_id, message=mess[1]
                )
            except Exception:
                error_msg = f"频道信息数组发送失败，消息内容如下\n\n{mess[1]}"
                logger.error(error_msg)
                await gv.admin_bot.send_private_msg(
                    user_id=gv.superuser_num, message=error_msg
                )
                break
    else:
        gv.channel_mess.clear()

    # 群聊消息
    if gv.handle_bot is not None and not gv.safe_mode and gv.group_mess:
        tmp = deepcopy(gv.group_mess)
        gv.group_mess.clear()

        for mess in tmp:
            try:
                await gv.handle_bot.send_group_msg(group_id=mess[0], message=mess[1])
            except Exception:
                gv.safe_mode = True
                error_msg = f"群聊信息数组发送失败，已临时关闭喵币系统并开启安全模式，消息内容如下\n\n{mess[1]}"
                logger.error(error_msg)
                await gv.admin_bot.send_private_msg(
                    user_id=gv.superuser_num, message=error_msg
                )
                break
    else:
        gv.group_mess.clear()


# 公告
@scheduler.scheduled_job("interval", minutes=45, jitter=60 * 10)
async def send_tips():
    if 8 <= datetime.now().hour <= 23:
        rows = await Tips.get_all_tip()
        msg = choice(rows)[1]
        gv.group_mess.append((gv.miao_group_num, msg))
        gv.channel_mess.append((gv.channel_id, msg))


# 每天早上8点报时
@scheduler.scheduled_job("cron", hour="8")
async def morning():
    gv.safe_mode = await Little_data.update_safe_mode(0)
    await sleep(3)
    gv.group_mess.append(
        (
            gv.miao_group_num,
            f"早上8点啦，喵喵起床干活啦[CQ:image,file={gv.site_url}/static/getup.jpg]",
        )
    )


# 每天晚上0点报时
@scheduler.scheduled_job("cron", hour="0")
async def night():
    gv.group_mess.append(
        (
            gv.miao_group_num,
            f"晚上12点别玩啦，喵喵要睡觉觉啦[CQ:image,file={gv.site_url}/static/sleep.jpg]",
        )
    )
    await sleep(3)
    gv.safe_mode = await Little_data.update_safe_mode(1)


# 每天中午12点列出待审查列表
@scheduler.scheduled_job("cron", hour="12")
async def zhb_scan():
    shencha_list = await Shencha.get_all()
    shencha_list_mess = "待审查列表" + "\n".join(shencha_list)
    gv.group_mess.append((gv.shencha_group_num, shencha_list_mess))
    gv.group_mess.append((gv.shencha_group_num, await check_group_zhb()))


# 随机喵币红包
@scheduler.scheduled_job("interval", minutes=45, jitter=60 * 15)
async def hongbao():
    if 8 <= datetime.now().hour < 23 and gv.miaobi_system:
        gv.packet = randint(333, 666)
        gv.packet_log = gv.packet
        gv.group_mess.append(
            (gv.miao_group_num, f"随机喵币红包，数量: {gv.packet}\n3分钟内发“抢喵币”瓜分红包")
        )
        gv.group_mess.append(
            (gv.miao_group2_num, f"随机喵币红包，数量: {gv.packet}\n3分钟内发“抢喵币”瓜分红包")
        )

        def _later():
            if gv.packet > 0:
                gv.group_mess.append((gv.miao_group_num, f"红包已过期，还有{gv.packet}个未瓜分"))
                gv.group_mess.append((gv.miao_group2_num, f"红包已过期，还有{gv.packet}个未瓜分"))
            gv.packet = 0
            gv.packet_once.clear()

        get_running_loop().call_later(180, _later)


# 每天0点释放字典内存和回收编号
@scheduler.scheduled_job("cron", hour="0")
async def auto_handle():
    try:
        # 清理内存

        # 身份验证
        tmp = deepcopy(gv.qq_verified)
        gv.qq_verified.clear()
        gv.qq_verified = tmp
        # 进群验证
        tmp = deepcopy(gv.join_check)
        gv.join_check.clear()
        gv.join_check = tmp

        gv.forward_once.clear()
        gv.rooms.clear()
        gv.online = 0

        await gv.save_some_data()
        gv.room_time.clear()
        gv.role_name.clear()
        gv.room_name.clear()
        gv.privacy.clear()
        gv.black.clear()
        gv.join_limit.clear()
        gv.version_set.clear()
        await gv.load_some_data()

        # 每月1号清理IP记录
        if datetime.now().day == 1:
            await Visit.clear_ip()

        # 刷新剩余天数
        rows = await Wg.get_all_bind_info()
        for wgnum, qqnum, ttl, numtype, played in rows:
            if numtype == "赞助" and await Sponsor.get_money(qqnum) >= 200:
                await Wg.update_ttl_by_wgnum(wgnum, 999)
            elif played:
                if numtype == "体验":
                    await Gold.update_expday(qqnum)
                    ttl = 7
                elif numtype == "普通":
                    ttl = 30
                elif numtype == "赞助":
                    ttl = 60
                await Wg.update_ttl_by_wgnum(wgnum, ttl)
            else:
                await Wg.update_ttl_by_wgnum(wgnum, ttl - 1)

        # 发送回收情况给服主
        output_text = f"昨天联机人次: {await Little_data.get_play_count_today()}\n昨天联机人数: {await Wg.get_players_count_today()}\n"
        # 联机人次更新重置
        await Little_data.update_play_count_daily()
        # 活跃玩家数量重置
        await Wg.reset_play_flag()
        # 红包发送次数重置
        await Gold.reset_packet_count()

        # 回收到期编号
        hs_dict = {}  # {qq:[wgnum,numtype]}
        rows = await Wg.get_all_bind_info()
        for wgnum, qqnum, ttl, numtype, played in rows:
            if ttl <= 0:
                hs_dict[qqnum] = [wgnum, numtype]
                await sleep(2)
                await release_wgnum(qqnum)

        # 群昵称编号修正
        if gv.admin_bot is not None:
            # 二群群员数据
            miao_group_1_member_data = await gv.admin_bot.get_group_member_list(
                group_id=gv.miao_group_num, no_cache=True
            )
            # 获取一群成员qq号
            for user in miao_group_1_member_data:
                wgnum = await Wg.get_wgnum_by_qq(user["user_id"])
                if wgnum != 0 and user["user_id"] != gv.superuser_num:
                    try:
                        # 特殊编号
                        if wgnum in gv.r2f.keys():
                            wgnum = gv.r2f[wgnum]
                        # 特殊编号
                        if user["card"].find(str(wgnum)) != 0:
                            await gv.admin_bot.set_group_card(
                                group_id=gv.miao_group_num,
                                user_id=int(user["user_id"]),
                                card=str(wgnum),
                            )
                            await sleep(3)
                    except Exception:
                        pass

        # 将长期不说话的人踢掉
        kick_count = 0
        if gv.admin_bot is not None:
            # 一群群员数据
            miao_group_1_member_data = await gv.admin_bot.get_group_member_list(
                group_id=gv.miao_group_num, no_cache=True
            )
            # 30天前的时间戳
            thirty_days_ago = int(
                datetime.timestamp(datetime.now() - timedelta(days=30))
            )
            for user in miao_group_1_member_data:
                if user["last_sent_time"] < thirty_days_ago and not await Wg.num_bind(
                    user["user_id"]
                ):
                    # 如果赞助金额不足20元从赞助榜去掉
                    if not await Sponsor.vip_exist(user["user_id"]):
                        await Sponsor.delete_sponsor(user["user_id"])
                    await gv.admin_bot.set_group_kick(
                        group_id=gv.miao_group_num, user_id=user["user_id"]
                    )
                    kick_count += 1
                    await sleep(2)

            # 清理在二群不在一群的人
            # 一群群员数据
            miao_group_1_member_data = await gv.admin_bot.get_group_member_list(
                group_id=gv.miao_group_num, no_cache=True
            )
            await sleep(2)
            # 二群群员数据
            miao_group_2_member_data = await gv.admin_bot.get_group_member_list(
                group_id=gv.miao_group2_num, no_cache=True
            )
            # 获取一群成员qq号
            group_1_qq_list = set()
            for user in miao_group_1_member_data:
                group_1_qq_list.add(user["user_id"])
            # 遍历二群成员qq，如果不在一群的就踢出去
            for user in miao_group_2_member_data:
                if user["user_id"] not in group_1_qq_list:
                    await gv.admin_bot.set_group_kick(
                        group_id=gv.miao_group2_num, user_id=user["user_id"]
                    )

            # 每周一检查一遍有没有编号回收疏漏
            if datetime.now().weekday() == 0:
                rows = await Wg.get_all_bind_info()
                for wgnum, qqnum, ttl, numtype, played in rows:
                    if not await check_in_group(qqnum):
                        hs_dict[qqnum] = [wgnum, numtype]
                        await release_wgnum(qqnum, True)
                    await sleep(2)

        if hs_dict:
            output_text += (
                f"玩家清理数: {kick_count}\n编号回收数: {len(hs_dict)}\n编号具体回收情况如下：\n"
                + "\n".join(
                    [
                        f"QQ{qqnum}-编号{hs_dict[qqnum][0]}({hs_dict[qqnum][1]})"
                        for qqnum in list(hs_dict)
                    ]
                )
            )

        # 刷新好友列表
        await refresh_friendlist()

        gv.private_mess.append((gv.superuser_num, output_text))

    except Exception:
        error_msg = f"自动回收函数出错!\n错误追踪:\n{format_exc()}"
        logger.error(error_msg)
        gv.private_mess.append((gv.superuser_num, error_msg))


@scheduler.scheduled_job("interval", seconds=5)
async def check_outdated():
    try:
        a, b = [int(x) for x in gv.wireguard_sub_gateway.split(".")]
        # 轮询房间信息
        def _get_room_info(i, j):
            # 发送数据包
            src_addr = [a, b, 255, 1]
            dst_addr = [a, b, i, j]
            gv.send_socket.send(
                # 由于大部分数据都可以固定的，所以直接用数字
                pack(
                    "!BBHHHBBH4B4B",
                    69,  # 头部长度和版本
                    0,  # 服务
                    36,  # 数据包总长度
                    8888,  # 标识
                    16384,  # flags和offset
                    64,  # ttl
                    17,  # 协议
                    get_checksum(
                        pack(
                            "!BBHHHBBH4B4B",
                            69,  # 头部长度和版本
                            0,  # 服务
                            36,  # 数据包总长度
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
                + pack("!HHHH", gv.room_scan_port, 46797, 16, 0)  # 源端口 目的端口 UDP长度 校验和
                + b"\xc4\x20\xb7\xe6\x7c\x3d\x25\x2b"  # 数据
            )

        # 轮询房间信息
        send_cir = gv.get_wgnum_count // 255
        res_count = gv.get_wgnum_count % 255
        for i in range(0, send_cir + 1):
            if i != send_cir:
                for j in range(1, 256):
                    _get_room_info(i, j)
            else:
                for j in range(1, res_count + 1):
                    _get_room_info(i, j)

        # syn半连接扫描房主端口是否开放
        for i in list(gv.rooms):
            a, b, c, d = [int(x) for x in i.split(".")]
            dst_addr = [a, b, c, d]
            src_addr = [a, b, 255, 1]
            gv.send_socket.send(
                # 由于大部分数据都可以固定的，所以直接用数字
                pack(
                    "!BBHHHBBH4B4B",
                    69,  # 头部长度和版本
                    0,  # 服务
                    40,  # 数据包总长度
                    8888,  # 标识
                    16384,  # flags和offset
                    64,  # ttl
                    6,  # 协议
                    get_checksum(
                        pack(
                            "!BBHHHBBH4B4B",
                            69,  # 头部长度和版本
                            0,  # 服务
                            40,  # 数据包总长度
                            8888,  # 标识
                            16384,  # flags和offset
                            64,  # ttl
                            6,  # 协议
                            0,  # 校验和
                            *src_addr,  # 源IP
                            *dst_addr,  # 目的IP
                        )
                    ),
                    *src_addr,  # 源IP
                    *dst_addr,  # 目的IP
                )
                + pack(
                    "!HHIIBBHHH",
                    gv.room_scan_port,  # 源端口
                    6797,  # 目的端口
                    1212121212,  # seq
                    0,  # ack
                    80,  # 头部长度
                    2,  # flags
                    64860,  # 窗口大小
                    get_checksum(
                        pack(
                            "!4B4BHHHHIIBBHHH",
                            *src_addr,  # 源IP
                            *dst_addr,  # 目的IP
                            6,  # 协议类型
                            20,  # tcp总长度
                            gv.room_scan_port,  # 源端口
                            6797,  # 目的端口
                            1212121212,  # seq
                            0,  # ack
                            80,  # 头部长度
                            2,  # flags
                            64860,  # 窗口大小
                            0,  # 校验和
                            0,  # 紧急指针
                        )
                    ),
                    0,  # 紧急指针
                )
            )

        def _later():
            # 更新实时联机人数
            count = 0
            for fangzhu in list(gv.rooms):
                count += len(list(gv.rooms[fangzhu][0])) + 1
            gv.online = count

            # 判断队友状态
            for fangzhu in list(gv.rooms):
                for chengyuan in list(gv.rooms[fangzhu][0]):
                    # 权值-1,如果加入者权值0就是断开了
                    if gv.rooms[fangzhu][0][chengyuan] > 0:
                        gv.rooms[fangzhu][0][chengyuan] -= 1
                    else:
                        gv.rooms[fangzhu][0].pop(chengyuan)
                        if chengyuan in gv.rooms[fangzhu][1]:
                            gv.rooms[fangzhu][1].remove(chengyuan)

            # 判断房间状态
            for fangzhu in list(gv.rooms):
                # 每轮减一次房间ttl
                if gv.rooms[fangzhu][3] > 0:
                    # 游戏中就-3，等待中就-1
                    if gv.room_time[fangzhu][0] == 0:
                        gv.rooms[fangzhu][3] -= 1
                    else:
                        gv.rooms[fangzhu][3] -= 3
                else:
                    gv.rooms.pop(fangzhu)

            # 生成房间列表图片
            results = []
            results_true = []
            results_false = []
            # { 房主IP str : [ {加入者IP : [角色, 存活]} dict , [已提醒进房提醒的IP] , 未定义 , 存活 int, 原始信息 str ]  }
            for fangzhu in list(gv.rooms):

                # 读取房间信息
                room_data = gv.rooms[fangzhu][4]
                room_info = loads(
                    bytes.fromhex(room_data[room_data.find("7b2273", 50) :]).decode()
                )

                # 判断是否为私有房
                if fangzhu in list(gv.privacy):
                    private_stat = "[私有]"
                else:
                    private_stat = ""

                # 获取房主信息
                fangzhu_wgnum = int(ip_to_wgnum(fangzhu))
                # 特殊编号
                if fangzhu_wgnum in gv.r2f.keys():
                    fangzhu_wgnum = gv.r2f[fangzhu_wgnum]
                # 特殊编号
                fangzhu_info = f"{fangzhu_wgnum}{gv.role_name[fangzhu]}"

                # 获取成员信息
                chengyuan_info = "暂无"
                if gv.rooms[fangzhu][0]:
                    chengyuan_info = ""
                    for chengyuan in list(gv.rooms[fangzhu][0]):
                        chengyuan_wgnum = int(ip_to_wgnum(chengyuan))

                        # 特殊编号
                        if chengyuan_wgnum in gv.r2f.keys():
                            chengyuan_wgnum = gv.r2f[chengyuan_wgnum]
                        # 特殊编号
                        try:
                            chengyuan_info += (
                                f"{chengyuan_wgnum}{gv.role_name[chengyuan]}  "
                            )
                        except Exception:
                            pass
                            # chengyuan_info += f"{chengyuan_wgnum}未知  "

                # 判断是否自定义房名
                if fangzhu in list(gv.room_name):
                    room_name = gv.room_name[fangzhu]
                else:
                    room_name = f"{fangzhu_wgnum}号的房间"

                # 判断游戏状态
                if room_info["hsb"]:
                    if chengyuan_info == "暂无":
                        # 局域网直连的房跳过
                        if room_info["ccc"] != 1:
                            continue
                        else:
                            chengyuan_info = "孤军奋战ing"
                    rooms_stat = (
                        "已开始"
                        + str((int(time()) - gv.room_time[fangzhu][0]) // 60)
                        + "分钟"
                    )
                    results_true.append(
                        f"房间: v{room_info['v']}-{room_name}"
                        + f"\n房主: {fangzhu_info}  {rooms_stat}  {private_stat}"
                        + f"\n成员: {chengyuan_info}\n"
                    )
                else:
                    rooms_stat = "等待ing"
                    results_false.append(
                        f"房间: v{room_info['v']}-{room_name}"
                        + f"\n房主: {fangzhu_info}  {rooms_stat}  {private_stat}"
                        + f"\n成员: {chengyuan_info}\n"
                    )

            results = results_false + results_true

            # 输出图片文件
            width = 300
            font = ImageFont.truetype(f"www/static/msyh.ttc", 16)
            now = datetime.now()
            time_str = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
            image = Image.new("RGB", (width, 80 * len(results) + 36), (255, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.text(
                (117, 10),
                time_str,
                font=font,
                fill=(0, 0, 0),
            )
            if results:
                count = 0
                for text in results:
                    if text.find("已开始") == -1:
                        color = (0, 80, 0)  # 绿色
                    else:
                        color = (139, 0, 0)  # 红色
                    draw.text((20, (80 * count) + 36), text, font=font, fill=color)
                    count += 1
            else:
                draw.text(
                    (20, 10),
                    f"当前没有房间",
                    font=font,
                    fill=(0, 0, 0),
                )
            image.save(f"www/static/roomlist.gif", "gif")

        # 等3秒，等客户端返回数据
        get_running_loop().call_later(3, _later)

    except Exception:
        error_msg = f"5s循环函数出错!\n错误追踪:\n{format_exc()}"
        logger.error(error_msg)
        gv.private_mess.append((gv.superuser_num, error_msg))


# 定时保存缓存数据 禁言次数归零
@scheduler.scheduled_job("cron", minute="59")
async def cron_save_some_data():
    await gv.save_some_data()
    gv.jinyan_count = 0
