from tortoise import fields
from tortoise.models import Model
from tortoise.expressions import Q


class Gold(Model):
    qqnum = fields.IntField()
    money = fields.IntField()
    date = fields.TextField()
    con = fields.IntField()
    packet = fields.IntField()

    ########################
    # 增加
    ########################
    # 创建用户
    @classmethod
    async def create_info(cls, qqnum: int):
        await cls.create(qqnum=qqnum, money=0, date="2022-01-01", con=0, packet=0)

    ########################
    # 删除
    ########################
    # 删除用户
    @classmethod
    async def delete_info(cls, qqnum: int) -> int:
        return await cls.filter(qqnum=qqnum).limit(1).delete()

    ########################
    # 查询
    ########################
    # 获取总金额
    @classmethod
    async def get_money_sum(cls) -> int:
        rows = await cls.filter().values_list("money")
        smoney = 0
        for row in rows:
            smoney += row[0]
        return smoney

    # 获取金额排行
    @classmethod
    async def get_rank(cls) -> list:
        rows = (
            await cls.filter().order_by("-money").limit(6).values_list("qqnum", "money")
        )
        return rows

    # 判断用户是否存在
    @classmethod
    async def info_exist(cls, qqnum: int) -> bool:
        if await cls.filter(qqnum=qqnum).limit(1).exists():
            return True
        else:
            return False

    # 获取余额
    @classmethod
    async def get_money(cls, qqnum: int) -> int:
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("money")
        if row:
            return row[0][0]
        else:
            await cls.create_info(qqnum)
            return 0

    # 获取签到信息
    @classmethod
    async def get_sign_info(cls, qqnum: int) -> tuple[int, str, int]:
        if not await cls.info_exist(qqnum):
            await cls.create_info(qqnum)
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("money", "date", "con")
        return (row[0][0], row[0][1], row[0][2])

    # 获取红包发送次数
    @classmethod
    async def get_packet_count(cls, qqnum: int) -> int:
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("packet")
        return row[0][0]

    ########################
    # 修改
    ########################
    # 转账
    @classmethod
    async def transfer(cls, f: int, t: int, money: int) -> int:
        f_money = await cls.get_money(f)
        if f_money >= money:
            if await cls.info_exist(t):
                await cls.change_money(f, money, False)
                await cls.change_money(t, money, True)
                return 1
            else:
                return -1
        else:
            return 0

    # 设置金额
    @classmethod
    async def set_money(cls, qqnum: int, money: int):
        if not await cls.info_exist(qqnum):
            await cls.create_info(qqnum)
        await cls.filter(qqnum=qqnum).limit(1).update(money=money)

    # 改变金额
    @classmethod
    async def change_money(cls, qqnum: int, money: int, increase: bool) -> bool:
        old_money = await cls.get_money(qqnum)
        if increase:
            await cls.filter(qqnum=qqnum).limit(1).update(money=old_money + money)
        else:
            await cls.filter(qqnum=qqnum).limit(1).update(money=old_money - money)

    # 更新签到信息
    @classmethod
    async def update_sign_info(cls, qqnum: int, money: int, date: str, con: int):
        await cls.filter(qqnum=qqnum).limit(1).update(money=money, date=date, con=con)

    # 更新红包发送次数
    @classmethod
    async def update_packet_count(cls, qqnum: int):
        c = await cls.get_packet_count(qqnum)
        await cls.filter(qqnum=qqnum).limit(1).update(packet=c + 1)

    # 重置红包发送次数
    @classmethod
    async def reset_packet_count(cls):
        await cls.filter(Q(packet__not=0)).update(packet=0)

    class Meta:
        table = "gold"
