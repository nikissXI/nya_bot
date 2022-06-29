from random import randint

from nonebot.log import logger
from src.models._gold import Gold
from src.models._sponsor import Sponsor
from src.models._wg import Wg
from src.models._xl import XLboard

from .global_var import gv
from .utils import check_in_group, exec_shell, set_group_card, wgnum_to_ip, write_bd_log


async def get_wgnum_count():
    gv.get_wgnum_count = await Wg.get_wgnum_count()
    logger.success(f"从数据库加载编号{gv.get_wgnum_count}个")


async def refresh_friendlist():
    if gv.bot_1 is not None:
        get_all_sponsor_info = {}
        rows = await Sponsor.get_all_vip_info()
        for row in rows:
            get_all_sponsor_info[row[0]] = wgnum_to_ip(row[1])
        gv.friendlist.clear()
        gv.vip_ip.clear()
        data = await gv.bot_1.get_friend_list()
        for i in data:
            qq = i["user_id"]
            if qq in get_all_sponsor_info.keys():
                gv.friendlist[qq] = get_all_sponsor_info[qq]
                gv.vip_ip[get_all_sponsor_info[qq]] = qq
        logger.success(f"共加载{len(gv.friendlist)}个好友")
    else:
        gv.friendlist.clear()
        gv.vip_ip.clear()
        logger.error("主bot未连接，已关闭私聊功能")


async def bd_wgnum(qqnum: int, wgnum: int, numtype: str) -> tuple[str, str]:
    out_mess = []
    # 普通绑定,编号使用可用编号中不小于10且最小的
    if wgnum == 0:
        # 获取待分配编号
        wgnum = await get_unuse_wgnum()
        key = await access_wgnum(qqnum, wgnum, numtype)
        out_mess.append(f"绑定成功<br />QQ: {qqnum}<br />编号: {wgnum}")
        # 刷新好友信息
        await refresh_friendlist()
        return ("<br />".join(out_mess), key)

    # 指定绑定的编号(特绑，需要检查编号原来是否有人)
    else:
        # 抢占他人编号
        if await Wg.num_bind(wgnum) and qqnum != await Wg.get_qq_by_wgnum(wgnum):
            o_wgnum, o_qqnum, o_ttl, o_numtype = await Wg.get_info_by_wgnum(wgnum)
            # 获取待分配编号
            new_wgnum = await get_unuse_wgnum()
            await change_wgnum(new_wgnum, o_wgnum, o_qqnum, o_ttl, o_numtype)
            out_mess.append(f"注意: {o_qqnum}的编号{o_wgnum}>>{new_wgnum}<br />")

        # 更改原编号
        if await Wg.num_bind(qqnum):
            o_wgnum, o_qqnum, o_ttl, o_numtype = await Wg.get_info_by_wgnum(qqnum)
            await change_wgnum(wgnum, o_wgnum, o_qqnum, o_ttl, o_numtype)
            out_mess.append(f"绑定成功<br />QQ: {qqnum}<br />编号: {o_wgnum}>>{wgnum}")

        # 新绑定
        else:
            out_mess.append(f"绑定成功<br />QQ: {qqnum}<br />编号: {wgnum}")
            await access_wgnum(qqnum, wgnum, numtype)
        # 刷新好友信息
        await refresh_friendlist()
        return ("<br />".join(out_mess), "")


# 获取可用编号
async def get_unuse_wgnum() -> int:
    wgnum = await Wg.get_a_usable_wgnum()
    if wgnum:
        return wgnum
    else:
        await auto_expend_wgnum()
        return await get_unuse_wgnum()


# 编号不足时自动扩充10个
async def auto_expend_wgnum():
    maxnum = gv.get_wgnum_count + 10
    for i in range(gv.get_wgnum_count + 1, maxnum + 1):
        await Wg.create_wgnum(i)
        await get_new_key(i)
    gv.get_wgnum_count = maxnum
    await get_wgnum_count()


# 刷新配置文件下载链接
async def get_new_key(wgnum: int) -> str:
    # 刷新配置文件
    ip = wgnum_to_ip(wgnum)
    code, stdout, stderr = await exec_shell(
        f"bash src/shell/wg_renew.sh renew {gv.wireguard_host} {gv.wireguard_port} {gv.wireguard_sub_gateway} {ip}"
    )
    if code:
        logger.error(f"{wgnum}号配置刷新失败")
    else:
        logger.success(f"{wgnum}号配置刷新")

    # 生成随机码
    base_str = "abcdefghigklmnopqrstuvwxyz0123456789"
    length = len(base_str) - 1
    key = ""
    for i in range(16):
        key += base_str[randint(0, length)]
    await Wg.update_key_by_wgnum(wgnum, key)
    return key


# 普通绑定
async def access_wgnum(qqnum: int, wgnum: int, numtype: str) -> str:
    if numtype == "体验":
        ttl = 7
    elif numtype == "普通":
        ttl = 30
    elif numtype == "赞助":
        ttl = 60

    await Sponsor.update_wgnum(qqnum, wgnum)
    key = await Wg.get_key_by_wgnum(wgnum)
    await Wg.update_info_by_wgnum(wgnum, qqnum, ttl, numtype, 0)
    # 特殊编号
    if wgnum in gv.r2f.keys():
        wgnum = gv.r2f[wgnum]
    # 特殊编号
    await set_group_card(qqnum, wgnum)
    await write_bd_log(qqnum, wgnum)
    return key


# 更换编号迁移信息
async def change_wgnum(
    new_wgnum: int,
    wgnum: int,
    qqnum: int,
    ttl: int,
    numtype: str,
):
    # 将旧编号信息转移到新编号并释放旧编号
    wgnum_ip = wgnum_to_ip(wgnum)
    new_wgnum_ip = wgnum_to_ip(new_wgnum)
    if wgnum_ip in list(gv.black):
        gv.black[new_wgnum_ip] = gv.black[wgnum_ip]
        gv.black.pop(wgnum_ip)
    if wgnum_ip in list(gv.join_limit):
        gv.join_limit[new_wgnum_ip] = gv.join_limit[wgnum_ip]
        gv.join_limit.pop(wgnum_ip)
    if wgnum_ip in list(gv.privacy):
        gv.privacy[new_wgnum_ip] = gv.privacy[wgnum_ip]
        gv.privacy.pop(wgnum_ip)
    if wgnum_ip in list(gv.version_set):
        gv.version_set[new_wgnum_ip] = gv.version_set[wgnum_ip]
        gv.version_set.pop(wgnum_ip)
    if wgnum_ip in list(gv.room_name):
        gv.room_name[new_wgnum_ip] = gv.room_name[wgnum_ip]
        gv.room_name.pop(wgnum_ip)
    for host_ip in list(gv.black):
        if wgnum_ip in gv.black[host_ip]:
            gv.black[host_ip].remove(wgnum_ip)
            gv.black[host_ip].append(new_wgnum_ip)
    # 刷新key
    await get_new_key(wgnum)
    played = await Wg.get_play_flag_by_wgnum(wgnum)
    await Wg.update_info_by_wgnum(wgnum, 0, 0, "", 0)

    # 如果有赞助更新赞助信息的编号
    await Sponsor.update_wgnum(qqnum, new_wgnum)
    # 如果有上修罗榜，更新编号
    await XLboard.update_wgnum(wgnum, new_wgnum)
    # 更新编号信息
    await Wg.update_info_by_wgnum(new_wgnum, qqnum, ttl, numtype, played)
    await write_bd_log(qqnum, new_wgnum)

    # 特殊编号
    if new_wgnum in gv.r2f.keys():
        new_wgnum = gv.r2f[new_wgnum]
    # 特殊编号
    await set_group_card(qqnum, new_wgnum)


# 释放编号
async def release_wgnum(qqnum: int, tuiqun: bool = False):
    wgnum = await Wg.get_wgnum_by_qq(qqnum)
    wgnum_ip = wgnum_to_ip(wgnum)
    if wgnum_ip in list(gv.black):
        gv.black.pop(wgnum_ip)
    if wgnum_ip in list(gv.join_limit):
        gv.join_limit.pop(wgnum_ip)
    if wgnum_ip in list(gv.privacy):
        gv.privacy.pop(wgnum_ip)
    if wgnum_ip in list(gv.version_set):
        gv.version_set.pop(wgnum_ip)
    if wgnum_ip in list(gv.room_name):
        gv.room_name.pop(wgnum_ip)
    if wgnum_ip in list(gv.room_time):
        gv.room_time.pop(wgnum_ip)
    if wgnum_ip in list(gv.role_name):
        gv.role_name.pop(wgnum_ip)
    for host_ip in list(gv.black):
        # 将设置的黑名单移除
        if wgnum_ip in gv.black[host_ip]:
            gv.black[host_ip].remove(wgnum_ip)
            # 如果黑名单空了就直接删除
            if not gv.black[host_ip]:
                gv.black.pop(host_ip)

    # 如果有赞助,就把名单中编号改为0
    await Sponsor.update_wgnum(qqnum, 0)
    # 修罗榜删除
    await XLboard.delete_xl_info(wgnum)
    # 刷新key
    await get_new_key(wgnum)
    # 删除编号信息
    await Wg.update_info_by_wgnum(wgnum, 0, 0, "", 0)
    # 刷新好友信息
    await refresh_friendlist()
    # 重置群名片, 退群的就不需要
    if tuiqun is False:
        await set_group_card(qqnum)


async def check_num(num: int) -> str:
    # 特殊编号
    if num in gv.f2r.keys():
        num = gv.f2r[num]
    # 特殊编号

    # 判断记录是否存在
    if await Wg.num_bind(num):
        wgnum, qqnum, ttl, numtype = await Wg.get_info_by_wgnum(num)

        # 特殊编号
        if wgnum in gv.r2f.keys():
            wgnum = gv.r2f[wgnum]
        # 特殊编号

        re_tip = f"<br />联机后次日刷新天数"
        if numtype == "赞助":
            money = await Sponsor.get_money(qqnum)
            numtype = f"赞助{money}元"
            if money >= 200:
                ttl = "∞"
                re_tip = ""
        elif numtype == "体验":
            expday = await Gold.get_expday(qqnum)
            numtype = f"已白嫖{expday}天"

        return f"QQ: {qqnum}<br />编号: {wgnum} ({numtype})<br />剩余天数: {ttl}天{re_tip}"

    # 如果没编号就查询是否有赞助信息
    elif await Sponsor.sponsor_exist(num):
        money = await Sponsor.get_money(num)

        # 判断是否在群里
        if await check_in_group(num):
            ex = ""
        else:
            ex = "<br />已退群"

        return f"QQ: {num}<br />编号: 无<br />赞助金额: {money}{ex}"

    # 无绑定信息
    else:
        return "无绑定信息"
