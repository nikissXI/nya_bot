from asyncio import create_task
from fastapi.middleware.cors import CORSMiddleware
from nonebot import get_asgi
from nonebot.log import logger
from src.models._guide import Guide
from src.models._little_data import Little_data
from src.models._nofree import Nofree
from src.models._sponsor import Sponsor
from src.models._visit import Visit
from src.models._gold import Gold
from src.models._wg import Wg
from src.models._xl import XLboard
from src.models._zhb_list import Zhb_list
from src.models._zhb_user import Zhb_user
from starlette.requests import Request
from starlette.responses import FileResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from ujson import loads
from re import match
from .config import (
    bd_api,
    black_api,
    cb_api,
    guide_api,
    jb_api,
    join_limit_api,
    krsr_api,
    privacy_api,
    room_name_api,
    version_set_api,
    xl_api,
    zhb_api,
    zz_api,
)
from .global_var import gv
from .utils import (
    check_in_group,
    exec_shell,
    get_wg_content,
    ip_to_wgnum,
    network_status,
    ping,
    server_status,
    wgnum_to_ip,
    write_ip_log,
)
from .wgnum import bd_wgnum, check_num

app = get_asgi()
templates = Jinja2Templates(directory=f"www")


async def start_web_server():
    # 挂载静态文件目录
    app.mount("/static", StaticFiles(directory=f"www/static"), name="static")
    app.mount("/cdn", StaticFiles(directory=f"www/static/cdn"), name="cdn")
    # 后台api允许跨域
    app.add_middleware(CORSMiddleware, allow_origins=["*"])
    logger.success("网页服务模块加载成功")


###################################
# 其他
###################################
@app.get("/channel")
async def channel(request: Request):
    return templates.TemplateResponse("channel.html", {"request": request})


@app.get("/robots.txt")
async def channel(request: Request):
    return templates.TemplateResponse("robots.txt", {"request": request})


# @app.get("/ip_log")
# async def ip_log(y=None, m=None, k=None):
#     if y and m and k == gv.secret_key:
#         file = f"log/ip_log/{y}-{m}.txt"
#         return FileResponse(file, filename=f"{y}-{m}.txt")
#     else:
#         return


###################################
# 规则阅读
###################################
@app.get("/rule")
async def rule(request: Request):
    return templates.TemplateResponse(
        "rule.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/rule_read")
async def rule_read(qqnum):
    if gv.admin_bot is None:
        return {"code": -2}
    try:
        qqnum = int(qqnum)
        c = await Gold.get_read_flag(qqnum)
        # 确认
        if c == 0:
            await Gold.update_read_flag(qqnum)
            await gv.admin_bot.set_group_ban(
                group_id=gv.miao_group_num, user_id=qqnum, duration=0
            )
            return {"code": 0}
        # 阅读过了
        elif c == 1:
            return {"code": 1}
        else:
            return {"code": -1}
    except Exception:
        # 不存在或非数字
        return {"code": -1}


###################################
# 官网首页
###################################
@app.get("/")
async def index(request: Request):
    # ip = request.client.host
    try:
        ip = request.headers["x-forwarded-for"]
        if not await Visit.ip_exist(ip):
            await Visit.create_ip(ip)
            await Little_data.update_web_visit_count()
    except KeyError:
        pass

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "yestoday_play_count": await Little_data.get_play_count_yestoday(),
            "today_play_count": await Little_data.get_play_count_today(),
            "vistor_count": await Little_data.get_web_visit_count(),
            "online_count": gv.online,
            "video_url": gv.video_url,
            "cdn_url": gv.cdn_url,
        },
    )


@app.get("/guide")
async def guide(request: Request):
    return templates.TemplateResponse(
        "guide.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/guide_data")
async def guide_data():
    rows = await Guide.get_guide()
    return {"data": rows}


@app.get("/sponsor")
async def sponsor(request: Request):
    return templates.TemplateResponse(
        "sponsor.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/sponsor_data")
async def sponsor_data():
    rows = await Sponsor.get_all_sponsor_info()
    # 特殊编号
    tmp = []
    for row in rows:
        tmp.append(list(row))
    rows = tmp
    for row in rows:
        if row[2] in gv.r2f.keys():
            row[2] = gv.r2f[row[2]]
    # 特殊编号
    return {"data": rows}


@app.get("/xl")
async def xl(request: Request):
    return templates.TemplateResponse(
        "xl.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/xl_data")
async def xl_data():
    rows = await XLboard.get_all_info()
    # 特殊编号
    tmp = []
    for row in rows:
        tmp.append(list(row))
    rows = tmp
    for row in rows:
        if row[0] in gv.r2f.keys():
            row[0] = gv.r2f[row[0]]
    # 特殊编号
    return {"data": rows}


@app.get("/zhb")
async def zhb(request: Request):
    return templates.TemplateResponse(
        "zhb.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/zhb_data")
async def zhb_data(qqnum=None):
    rows = await Zhb_list.get_all_info(qqnum)
    return {"data": rows}


@app.get("/zhb_check")
async def zhb_check(qqnum):
    if await Zhb_list.qq_exist(int(qqnum)):
        return {"code": 1}
    else:
        return {"code": 0}


@app.get("/zhb_add")
async def zhb_add(key, qqnum, why, paths):
    author = await Zhb_user.get_nick_by_pass(key)
    if author:
        try:
            qq = int(qqnum)
        except Exception:
            return {"code": -1, "msg": "请正确填写QQ号"}

        try:
            loads(paths)
        except Exception:
            return {"code": -1, "msg": "图片上传出错"}

        await Zhb_list.create_info(qq, author, why, paths)
        gv.group_mess.append(
            (gv.shencha_group_num, f"{author}发布了黑名单\n{gv.site_url}/why?qq={qq}")
        )

        gv.group_mess.append(
            (gv.miao_group_num, f"{author}发布了黑名单\n{gv.site_url}/why?qq={qq}")
        )
        return {"code": 0, "msg": "提交信息成功！"}

    else:
        return {"code": -1, "msg": "key错误！"}


@app.get("/why")
async def why(request: Request):
    return templates.TemplateResponse(
        "why.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/why_data")
async def why_data(qqnum=None):
    if qqnum is not None:
        if await Zhb_list.qq_exist(qqnum):
            qqnum, time, why, path = await Zhb_list.get_why(qqnum)
            return {"qqnum": qqnum, "time": time, "why": why, "path": path}
        else:
            return {"qqnum": 0}
    else:
        return {"qqnum": 0}


###################################
# 编号配置
###################################
@app.get("/get")
async def get(request: Request):
    return templates.TemplateResponse(
        "get.html",
        {
            "request": request,
            "cdn_url": gv.cdn_url,
            "join_group_url": gv.join_group_url,
        },
    )


@app.get("/submit_qq")
async def submit_qq(request: Request, qq=None, app=None):
    if qq:
        ip = request.headers["x-forwarded-for"]
        try:
            qq = int(qq)
        except Exception:
            return {"code": 0, "msg": "请正确填写QQ号"}

        # 判断是否在黑名单
        if qq in await Zhb_list.get_all_qq():
            return {"code": -1}

        # 提交了qq并发送了确认，状态码1-4
        if (
            qq in gv.qq_verified.keys()
            and gv.qq_verified[qq][0] == ip
            and gv.qq_verified[qq][1] == True
        ):
            # 记录IP
            create_task(write_ip_log(qq, ip))

            # 体验号,状态码1
            if gv.qq_verified[qq][2] == "体验号":
                gv.qq_verified.pop(qq)
                res, key = await bd_wgnum(qq, 0, "体验")

            # 赞助号,状态码1
            elif gv.qq_verified[qq][2] == "赞助号":
                gv.qq_verified.pop(qq)
                res, key = await bd_wgnum(qq, 0, "赞助")

            # 获取链接,状态码1
            elif gv.qq_verified[qq][2] == "拿链接":
                # 顺便重载一下
                wgnum = await Wg.get_wgnum_by_qq(qq)
                code, stdout, stderr = await exec_shell(
                    f"bash src/shell/wg_renew.sh readd {wgnum_to_ip(wgnum)}"
                )
                gv.qq_verified.pop(qq)
                key = await Wg.get_key_by_wgnum(qq)

            if app:
                wgnum = await Wg.get_wgnum_by_qq(qq)
                wg_ip = wgnum_to_ip(wgnum)
                content = await get_wg_content(wg_ip)
                # 特殊编号
                if wgnum in gv.r2f.keys():
                    wgnum = gv.r2f[wgnum]
                # 特殊编号
                return {
                    "code": 1,
                    "content": content,
                    "tunnel_name": str(wgnum),
                }
            else:
                return {"code": 1, "link": f"{gv.site_url}/config?k={key}"}

        # 提交了qq还没发送确认,状态码4
        elif (
            qq in gv.qq_verified.keys()
            and gv.qq_verified[qq][0] == ip
            and gv.qq_verified[qq][1] == False
        ):
            return {"code": 4}

        # 判断机器人是否离线
        if gv.admin_bot is None:
            return {"code": -4}

        # 判断是否在群里
        if not await check_in_group(qq):
            return {"code": 5}

        # 提交了qq但IP地址不同，重置
        if qq in gv.qq_verified.keys() and gv.qq_verified[qq][0] != ip:
            gv.qq_verified.pop(qq)

        # 判断是否有编号,状态码6
        if await Wg.num_bind(qq):
            gv.qq_verified[qq] = [ip, False, "拿链接"]
            return {"code": 6}
        # 判断是否为赞助号,状态码7
        elif await Sponsor.sponsor_exist(qq):
            gv.qq_verified[qq] = [ip, False, "赞助号"]
            return {"code": 7}
        # 判断是否在白嫖列表中
        if await Nofree.qqnum_exist(qq):
            return {"code": -2}
        # 都不符合就给体验号
        else:
            # 判断QQ等级是否为10级以上
            user_data = await gv.admin_bot.get_stranger_info(user_id=qq, no_cache=True)
            # QQ等级不够，状态码-3
            if user_data["level"] <= 10:
                return {"code": -3}
            # 够等级就给体验号,状态码7
            else:
                gv.qq_verified[qq] = [ip, False, "体验号"]
                return {"code": 8}
    else:
        return "nothing"


@app.get("/config")
async def config(request: Request, k=None):
    bdmsg = qqnum = wgnum = ""
    if k:
        if await Wg.key_exist(k):
            wgnum, qqnum, numtype = await Wg.get_info_by_key(k)
            bdmsg = f"链接有效，绑定信息如下"
            # 特殊编号
            if wgnum in gv.r2f.keys():
                wgnum = gv.r2f[wgnum]
            # 特殊编号
            wgnum = f"编号：{wgnum} ({numtype})"
            qqnum = f"QQ：{qqnum}"
        else:
            bdmsg = f"链接无效，无法下载配置文件"

    return templates.TemplateResponse(
        "config.html",
        {
            "request": request,
            "bdmsg": bdmsg,
            "wgnum": wgnum,
            "qqnum": qqnum,
            "video_url": gv.video_url,
            "cdn_url": gv.cdn_url,
        },
    )


@app.get("/d")
async def d(request: Request, k=None):
    if k is None:
        return RedirectResponse(url="/")
    else:
        if await Wg.key_exist(k):
            wgnum, qqnum, numtype = await Wg.get_info_by_key(k)
            file = ""
            file = f"tunnel/conf/{wgnum_to_ip(wgnum)}.conf"
            # 特殊编号
            if wgnum in gv.r2f.keys():
                wgnum = gv.r2f[wgnum]
            # 特殊编号
            return FileResponse(file, filename=f"{wgnum}.conf")
        else:
            return templates.TemplateResponse(
                "get.html", {"request": request, "cdn_url": gv.cdn_url}
            )


@app.get("/num_check")
async def num_check(num=None):
    if num:
        try:
            num = int(num)
        except Exception:
            return {"msg": "请正确填写编号"}
        msg = await check_num(num)
        return {"msg": msg}
    else:
        return "nothing"


###################################
# 房间列表
###################################
@app.get("/room")
async def room(request: Request):
    return templates.TemplateResponse(
        "room.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/get_ip")
async def get_ip(wgnum=None):
    try:
        wgnum = int(wgnum)
    except Exception:
        return {"msg": "请输入正确的编号"}
    if wgnum:
        # 特殊编号
        if wgnum in gv.f2r.keys():
            wgnum = gv.f2r[wgnum]
        # 特殊编号
        msg = wgnum_to_ip(wgnum)
        return {"msg": msg}
    else:
        return {"msg": "请输入正确的编号"}


###################################
# 玩家后台
###################################
@app.get("/bk")
async def bk(request: Request):
    return templates.TemplateResponse(
        "bk.html",
        {
            "request": request,
            "cdn_url": gv.cdn_url,
            "gateway": gv.wireguard_gateway,
            "port": gv.port,
        },
    )


@app.get("/bk_data")
async def bk_data(request: Request):
    if request.client.host.find(gv.wireguard_sub_gateway) != -1:

        ip = request.client.host
        wgnum = int(ip_to_wgnum(ip))

        wgnum, qqnum, ttl, numtype = await Wg.get_info_by_wgnum(wgnum)

        if numtype == "体验":
            refuse = 1
        else:
            refuse = 0

        if ttl == 999:
            ttl = "∞"

        if ip in gv.room_name:
            fm = gv.room_name[ip]
        else:
            fm = ""

        code, res = await ping(ip, 1)
        if code:
            ms = 0
        else:
            ms = res[1]

        if ip in gv.privacy:
            sy = []
            for i in gv.privacy[ip]:
                m_wgnum = int(ip_to_wgnum(i))
                # 特殊编号
                if m_wgnum in gv.r2f.keys():
                    m_wgnum = gv.r2f[m_wgnum]
                # 特殊编号
                sy.append(str(m_wgnum))
            sy = " ".join(sy)
        else:
            sy = ""

        if ip in gv.black:
            lh = []
            for i in gv.black[ip]:
                m_wgnum = int(ip_to_wgnum(i))
                # 特殊编号
                if m_wgnum in gv.r2f.keys():
                    m_wgnum = gv.r2f[m_wgnum]
                # 特殊编号
                lh.append(str(m_wgnum))
            lh = " ".join(lh)
        else:
            lh = ""

        if ip in gv.join_limit:
            rs = gv.join_limit[ip]
        else:
            rs = ""

        if ip in gv.version_set:
            bb = gv.version_set[ip]
        else:
            bb = ""
        # 特殊编号
        if wgnum in gv.r2f.keys():
            wgnum = gv.r2f[wgnum]
        # 特殊编号
        data = {
            "wgnum": wgnum,
            "wgnum_type": numtype,
            "ttl": ttl,
            "ms": f"{ms}",
            "fm": f"{fm}",
            "sy": f"{sy}",
            "lh": f"{lh}",
            "rs": f"{rs}",
            "bb": f"{bb}",
            "refuse": refuse,
        }
        return data

    else:
        return "nothing"


@app.get("/bk_update")
async def bk_update(request: Request, fm=None, sy=None, lh=None, rs=None, bb=None):
    if request.client.host.find(gv.wireguard_sub_gateway) != -1:
        ip = request.client.host
        wgnum = int(ip_to_wgnum(ip))
        wgnum, qqnum, ttl, numtype = await Wg.get_info_by_wgnum(wgnum)
        if numtype == "体验":
            return {"msg": "wtf"}

        out_mess = []
        # 房名
        if fm != "" or (fm == "" and ip in list(gv.room_name)):
            res = await room_name_api(fm, ip)
            if res:
                out_mess.append(res)
        # 私有
        if sy != "" or (sy == "" and ip in list(gv.privacy)):
            res = await privacy_api(sy, ip)
            if res:
                out_mess.append(res)
        # 拉黑
        if lh != "" or (lh == "" and ip in list(gv.black)):
            res = await black_api(lh, ip)
            if res:
                out_mess.append(res)
        # 人数
        if rs != "" or (rs == "" and ip in list(gv.join_limit)):
            res = await join_limit_api(rs, ip)
            if res:
                out_mess.append(res)
        # 版本
        if bb != "" or (bb == "" and ip in list(gv.version_set)):
            res = await version_set_api(bb, ip)
            if res:
                out_mess.append(res)
        # 信息返回
        if out_mess:
            return {"msg": "\n".join(out_mess)}
        else:
            return {"msg": "无变更"}
    else:
        return "nothing"


###################################
# 检测
###################################
@app.get("/ms_check")
async def ms_check(request: Request, lx=None, wgnum=None):
    # 0是bk的延迟查询 1是瞬时检测 2是稳定检测 3是找卡比
    if lx == "0":
        code, data = await ping(request.client.host, 10)
        return {
            "ave_ms": data[1],
            "detail_ms": f"最低{data[0]}ms,最高{data[2]}ms,丢包{data[3]}%",
        }
    try:
        wgnum = int(wgnum)
    except Exception:
        return {"msg": "请填纯数字"}
    if lx == "1" and wgnum:
        msg = await network_status(wgnum, 1)
        return {"msg": msg}

    if lx == "2" and wgnum:
        msg = await network_status(wgnum, 2)
        return {"msg": msg}

    if lx == "3" and wgnum:
        msg = await network_status(wgnum, 3)
        return {"msg": msg}

    else:
        return "nothing"


@app.get("/http_ping")
async def http_ping(request: Request, wgnum=None):
    if request.client.host.find(gv.wireguard_sub_gateway) != -1:
        ip = request.client.host
        if wgnum == ip_to_wgnum(ip):
            return {"self": True}
        else:
            return {"self": False}
    else:
        return


@app.get("/force_ping")
async def force_ping(request: Request):
    if request.client.host.find(gv.wireguard_sub_gateway) != -1:
        ip = request.client.host
        return f"{ip_to_wgnum(ip)}已连接服务器"
    else:
        return "请连上服务器再访问"


###################################
# 服主后台
###################################
@app.get("/admin")
async def admin(request: Request):
    return templates.TemplateResponse(
        "admin.html", {"request": request, "cdn_url": gv.cdn_url}
    )


@app.get("/get_num")
async def get_num():
    wbd = await Wg.get_all_unbind_wgnum()
    fzz = await Wg.get_all_unsponsor_wgnum()
    return {
        "get_wgnum_count": f"可用编号数量: {gv.get_wgnum_count}",
        "player_count": f"今天活跃玩家数量: {await Wg.get_players_count_today()}人",
        "wbd": f"未绑定编号: {len(wbd)}个<br />{str(wbd)[1:-1]}",
        "fzz": f"非赞助编号: {len(fzz)}个<br />{str(fzz)[1:-1]}",
    }


@app.get("/bd_data")
async def bd_data(numtype=None):
    if numtype:
        rows = await Wg.get_all_info(numtype)
    else:
        rows = await Wg.get_all_bind_info()
    return {"data": rows}


@app.get("/admin_api")
async def admin_api(
    op_type=None,
    sub_op_type=None,
    num=None,
    value=None,
    key=None,
):
    if await Zhb_user.get_nick_by_pass(key) is not None:
        if op_type == "绑定记录":
            date = num
            c = match(r"\d{4}-\d{1,2}", date)
            if c is None:
                return {"msg": "日期格式错误"}

            qqnum = value
            if qqnum == "":
            #     return {"msg": "QQ号未填写"}
                qqnum = "*"
            code, stdout, stderr = await exec_shell(
                f"grep -E ' {qqnum} ' log/bd_log/{date}.txt"
            )
            if code:
                return {"msg": "无记录"}
            else:
                return {"msg": stdout.decode().replace("\n", "<br />")}

        elif op_type == "游戏记录":
            date = num
            c = match(r"\d{4}-\d{1,2}-\d{1,2}", date)
            if c is None:
                return {"msg": "日期格式错误"}
            wgnum = value
            if wgnum == "":
                # return {"msg": "编号未填写"}
                wgnum = "*"
            code, stdout, stderr = await exec_shell(
                f"grep -E ' {wgnum}号|入{wgnum}号' log/room_log/{date}.txt"
            )
            if code:
                return {"msg": "无记录"}
            else:
                return {"msg": stdout.decode().replace("\n", "<br />")}

    if key == gv.secret_key:
        if op_type == "IP记录":
            date = num
            c = match(r"\d{4}-\d{1,2}", date)
            if c is None:
                return {"msg": "日期格式错误"}
            qqnum = value
            if qqnum == "":
            #     return {"msg": "QQ号未填写"}
                qqnum = "*"
            code, stdout, stderr = await exec_shell(
                f"grep -E ' {qqnum} ' log/ip_log/{date}.txt"
            )
            if code:
                return {"msg": "无记录"}
            else:
                return {"msg": stdout.decode().replace("\n", "<br />")}

        if op_type == "功能开关":
            if sub_op_type == "安全模式":
                if value == "打开":
                    gv.safe_mode = True
                else:
                    gv.safe_mode = False

            elif sub_op_type == "喵币系统":
                if value == "打开":
                    gv.miaobi_system = True
                else:
                    gv.miaobi_system = False

            return {"msg": f"{sub_op_type}已{value}"}

        if op_type == "状态":
            res = await server_status()
            return {"msg": res}

        elif op_type == "黑名单管理":
            res = await zhb_api(sub_op_type, num, value)
            return {"msg": res}

        elif op_type == "文章管理":
            res = await guide_api(sub_op_type, num, value)
            return {"msg": res}

        if num:
            num = int(num)
        else:
            return {"msg": "参数缺失"}

        if op_type == "绑定":
            if value == "" or value is None or int(value) < 0:
                wgnum = 0
            else:
                wgnum = int(value)

            # 判断是否在群里
            if await check_in_group(num):
                res = await bd_api(num, wgnum)
                return {"msg": res}

            else:
                return {"msg": "人不在群里"}

        elif op_type == "查绑":
            res, link = await cb_api(num)
            return {"msg": res, "key": link}

        elif op_type == "赞助":
            money = value
            res = await zz_api(num, money)
            return {"msg": res}

        elif op_type == "解绑":
            res = await jb_api(num)
            return {"msg": res}

        elif op_type == "修罗榜":
            wgnum, xlnum = num, int(value)
            res = await xl_api(wgnum, xlnum)
            return {"msg": res}

        elif op_type == "扩容/缩容":
            res = await krsr_api(num)
            return {"msg": res}

        return {"msg": "干啥呢"}
    else:
        return {"msg": "key无效"}


###################################
# 关于喵服
###################################
@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse(
        "about.html", {"request": request, "cdn_url": gv.cdn_url}
    )
