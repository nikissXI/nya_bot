from re import search

from src.modules._guide import Guide
from src.modules._sponsor import Sponsor
from src.modules._wg import Wg
from src.modules._xl import XLboard
from src.modules._zhb_list import Zhb_list
from src.modules._zhb_user import Zhb_user

from .global_var import gv
from .utils import check_in_group, ip_to_wgnum, wgnum_to_ip
from .wgnum import (
    bd_wgnum,
    check_num,
    get_new_key,
    get_wgnum_count,
    refresh_friendlist,
    release_wgnum,
)


###################################
# 后台设置
###################################
async def room_name_api(name: str, ip: str) -> str:
    name = name.strip()
    if len(name) > 50:
        return "房名过长"
    elif name == "":
        if ip in list(gv.room_name):
            gv.room_name.pop(ip)
        return "房名恢复默认"
    elif ip in list(gv.room_name):
        if gv.room_name[ip] == name:
            return
        else:
            gv.room_name[ip] = name
            return f"房名设置为: {name}"
    else:
        gv.room_name[ip] = name
        return f"房名设置为: {name}"


async def privacy_api(data: str, ip: str) -> str:
    wgnum = int(ip_to_wgnum(ip))
    # 取消私有
    if data == "":
        if ip in list(gv.privacy):
            gv.privacy.pop(ip)
        return "清空私有列表成功，现在所有人都能搜到你的房间"
    else:
        try:
            data = data.strip().split()
            # 特殊编号
            for x in data[:]:
                x = int(x)
                if x in gv.f2r.keys():
                    data.remove(str(x))
                    data.append(str(gv.f2r[x]))
            # 特殊编号
            old_data = []
            # 判断以前是否设置过，如果设置过就把以前的取出来
            if ip in list(gv.privacy):
                for i in gv.privacy[ip]:
                    old_data.append(ip_to_wgnum(i))
            # 如果和旧数据一样，就不进行操作
            if data == old_data:
                return
            else:
                # 设置私有
                tmp = [int(x) for x in data if 1 <= int(x) <= gv.get_wgnum_count]
                members = []
                members_out = []
                # 去掉重复和自己的编号
                for i in tmp:
                    if i not in members_out and i != wgnum:
                        members.append(wgnum_to_ip(i))
                        # 特殊编号
                        if i in gv.r2f.keys():
                            i = gv.r2f[i]
                        # 特殊编号
                        members_out.append(i)

                if not members:
                    return "私有设置失败，目标为空"
                else:
                    gv.privacy[ip] = members
                    return f"只有{members_out}能搜到你房间"
        except Exception:
            return "私有设置失败，格式有误，编号用空格分割，如：12 32"


async def black_api(data: str, ip: str) -> str:
    wgnum = int(ip_to_wgnum(ip))
    # 取消拉黑
    if data == "":
        if ip in list(gv.black):
            gv.black.pop(ip)
        return "清空黑名单成功，如需要请重新设置"
    else:
        try:
            data = data.strip().split()
            # 特殊编号
            for x in data[:]:
                x = int(x)
                if x in gv.f2r.keys():
                    data.remove(str(x))
                    data.append(str(gv.f2r[x]))
            # 特殊编号
            old_data = []
            # 判断以前是否设置过，如果设置过就把以前的取出来
            if ip in list(gv.black):
                for i in gv.black[ip]:
                    old_data.append(ip_to_wgnum(i))
            # 如果和旧数据一样，就不进行操作
            if data == old_data:
                return
            else:
                # 设置拉黑
                tmp = [int(x) for x in data if 1 <= int(x) <= gv.get_wgnum_count]
                members = []
                members_out = []
                # 去掉重复和自己的编号
                for i in tmp:
                    if i not in members_out and i != wgnum:
                        members.append(wgnum_to_ip(i))
                        # 特殊编号
                        if i in gv.r2f.keys():
                            i = gv.r2f[i]
                        # 特殊编号
                        members_out.append(i)

                if not members:
                    return "黑名单设置失败，目标为空"
                else:
                    gv.black[ip] = members
                    return f"将禁止{members_out}搜到你房间"
        except Exception:
            return "黑名单设置失败，格式有误，编号用空格分割，如：12 32"


async def join_limit_api(data: str, ip: str) -> str:
    # 取消
    if data == "":
        if ip in list(gv.join_limit):
            gv.join_limit.pop(ip)
        return "房间人数上限已恢复默认"
    # 设置人数
    elif data == "2" or data == "3":
        if ip in gv.join_limit and gv.join_limit[ip] == data:
            return
        else:
            gv.join_limit[ip] = data
            return f"房间人数上限设置为{data}，注: 如果有人同时搜到你房间并加入会限制失败"
    else:
        return f"房间人数上限设置失败，格式有误，请填2或3"


async def version_set_api(data: str, ip: str) -> str:
    # 取消
    if data == "":
        if ip in list(gv.version_set):
            gv.version_set.pop(ip)
        return "房间列表版本已恢复默认"
    # 设置版本
    else:
        data = data.strip()
        if ip in list(gv.version_set) and gv.version_set[ip] == data:
            return
        else:
            result = search(r"^1\.\d{2}\.\d{1,2}$", data, flags=0)
            if result:
                gv.version_set[ip] = data
                return f"你搜到的房间版本都会强制转为{data}"
            else:
                return f"版本设置格式有误，请填如：1.11.1"


###################################
# 管理员接口
###################################
async def bd_api(qqnum: int, wgnum: int) -> str:
    if wgnum > gv.get_wgnum_count:
        return "编号无效"
    # 如果进行过自助拿号给去掉
    if qqnum in gv.qq_verified.keys():
        gv.qq_verified.pop(qqnum)

    # 已经有编号的
    if await Wg.num_bind(qqnum):
        o_wgnum, qqnum, ttl, numtype = await Wg.get_info_by_wgnum(qqnum)
        # 没指定编号并且是体验，直接升级普通号
        if wgnum == 0 and numtype == "体验":
            await Wg.update_ttl_and_numtype_by_wgnum(o_wgnum, 30, "普通")
            return f"{qqnum}升级为普通号"
        # 有指定编号
        elif wgnum != 0:
            # 如果是体验，先升级普通号，再进行绑定
            if numtype == "体验":
                await Wg.update_ttl_and_numtype_by_wgnum(o_wgnum, 30, "普通")
            res, key = await bd_wgnum(qqnum, wgnum, "")
            return res
        # 没指定编号且是普通或赞助，不操作
        else:
            return f"{qqnum}已经是普通号或赞助号"

    # 没有编号的
    else:
        if await Sponsor.sponsor_exist(qqnum):
            res, key = await bd_wgnum(qqnum, wgnum, "赞助")
        else:
            res, key = await bd_wgnum(qqnum, wgnum, "普通")
        return res


async def jb_api(num: int) -> str:
    # 特殊编号
    if num in gv.f2r.keys():
        num = gv.f2r[num]
    # 特殊编号
    if await Wg.num_bind(num):
        wgnum, qqnum, ttl, numtype = await Wg.get_info_by_wgnum(num)
        await release_wgnum(qqnum)
        return f"解绑成功<br />QQ: {qqnum}<br />编号: {wgnum}"
    else:
        return "目标不存在绑定信息"


async def cb_api(num: int) -> tuple[str, str]:
    # 特殊编号
    if num in gv.f2r.keys():
        num = gv.f2r[num]
    # 特殊编号

    # 获取链接
    if await Wg.num_bind(num):
        link = gv.site_url + "config?k=" + await Wg.get_key_by_wgnum(num)
    else:
        link = ""

    msg = await check_num(num)
    return (msg, link)


async def zz_api(qqnum: int, money: str) -> str:
    # 若存在记录则更新
    if await Sponsor.sponsor_exist(qqnum):
        old_money = await Sponsor.get_money(qqnum)

        if money == "0":
            if await Wg.num_bind(qqnum):
                wgnum = await Wg.get_wgnum_by_qq(qqnum)
                await Wg.update_ttl_and_numtype_by_wgnum(wgnum, 30, "普通")
                ex = f"<br />并降级为普通号"
            else:
                ex = ""
                # 如果进行过自助拿号给去掉
                if qqnum in gv.qq_verified.keys():
                    gv.qq_verified.pop(qqnum)

            await Sponsor.delete_sponsor(qqnum)
            await refresh_friendlist()
            return f"{qqnum}的赞助信息删除成功{ex}"

        if money == "" or money is None:
            return "赞助金额未填写"

        elif money[:1] == "+":
            money = old_money + int(money[1:])
        elif money[:1] == "-":
            money = old_money - int(money[1:])
            if money <= 0:
                return "钱都减没了"

        elif int(money) == old_money:
            return "没变化"

        else:
            money = int(money)

        await Sponsor.update_money(qqnum, money)
        if money >= 20:
            await refresh_friendlist()
        return f"{qqnum}的赞助信息更新成功<br />{old_money}元 >> {money}元"

    # 不存在则添加
    else:
        if money == "" or money is None or int(money) <= 0:
            return "赞助金额未填写"
        else:
            money = int(money)

        # 判断是否在群里
        if await check_in_group(qqnum):
            if await Wg.num_bind(qqnum):
                wgnum = await Wg.get_wgnum_by_qq(qqnum)
                await Wg.update_ttl_and_numtype_by_wgnum(wgnum, 60, "赞助")
                ex = f"<br />并升级为赞助号"
            else:
                # 如果进行过自助拿号给去掉
                if qqnum in gv.qq_verified.keys():
                    gv.qq_verified.pop(qqnum)
                wgnum = 0
                ex = ""

            await Sponsor.create_sponsor(qqnum, money, wgnum)
            if money >= 20:
                await refresh_friendlist()
            return f"{qqnum}的赞助信息添加成功 >> {money}元{ex}"

        else:
            return "人不在群里"


async def xl_api(wgnum: int, xlnum: int) -> str:
    # 特殊编号
    if wgnum in gv.f2r.keys():
        wgnum = gv.f2r[wgnum]
    # 特殊编号
    # 若存在记录则更新
    if await XLboard.get_xl_info(wgnum):
        if xlnum == 0:
            await XLboard.delete_xl_info(wgnum)
            return "删除成功"
        else:
            await XLboard.update_xl_info(wgnum, xlnum)
            # 特殊编号
            if wgnum in gv.r2f.keys():
                wgnum = gv.r2f[wgnum]
            # 特殊编号
            return f"{wgnum}号更新成功-修罗{xlnum}"
    else:
        if await Wg.num_bind(wgnum):
            await XLboard.create_xl_info(wgnum, xlnum)
            # 特殊编号
            if wgnum in gv.r2f.keys():
                wgnum = gv.r2f[wgnum]
            # 特殊编号
            return f"{wgnum}号上榜成功-修罗{xlnum}"
        else:
            return "编号未绑定或不存在"


async def krsr_api(num: int) -> str:
    # 扩容
    if num > gv.get_wgnum_count:
        # 如果0个编号，先+1
        if gv.get_wgnum_count == 0:
            gv.get_wgnum_count = 1

        for i in range(gv.get_wgnum_count + 1, num + 1):
            await Wg.create_wgnum(i)
            await get_new_key(i)
        diff = num - gv.get_wgnum_count
        gv.get_wgnum_count = num
        await get_wgnum_count()
        return f"当前最大编号是: {gv.get_wgnum_count}，共增加编号{diff}个"

    # 缩容
    elif num < gv.get_wgnum_count:
        # 号都没有缩什么
        if gv.get_wgnum_count == 0:
            return "一个号都没有缩什么"

        # 判断这个缩容范围的编号有没有在使用的
        elif await Wg.wgnum_in_range(num):
            return f"缩容范围内有编号被绑定着"

        # 没问题就缩容
        else:
            for i in range(num + 1, gv.get_wgnum_count + 1):
                await Wg.delete_wgnum(i)
            diff = gv.get_wgnum_count - num
            gv.get_wgnum_count = num
            await get_wgnum_count()
            return f"当前最大编号是: {gv.get_wgnum_count}，共减少编号{diff}个"

    # 相同
    else:
        return f"现在最大编号就是{gv.get_wgnum_count}"


async def zhb_api(op_type: str, qqnum: int = None, username: str = None) -> str:
    if op_type == "删除记录":
        if await Zhb_list.delete_info(qqnum):
            return f"删除{qqnum}的记录成功"
        else:
            return f"{qqnum}不存在记录"

    elif op_type == "列出账号":
        return await Zhb_user.get_all_user()

    elif op_type == "增加账号":
        return await Zhb_user.create_user(qqnum, username)

    elif op_type == "删除账号":
        return await Zhb_user.delete_user(qqnum)

    else:
        return "??????"


async def guide_api(op_type: str, str1: str, str2: str) -> str:
    if op_type == "增加":
        sort, title = str1.split(" ")
        author, link = str2.split(" ")
        if await Guide.create_guide(sort, title, author, link):
            gv.group_mess.append((gv.miao_group_num, f"有新的链接加入文章页面！\n{title}\n{link}"))
            return "增加成功"
        else:
            return "增加失败"
    elif op_type == "删除":
        if await Guide.delete_guide(int(str1)):
            return "删除成功"
        else:
            return "删除失败"
    else:
        return "？？？"
