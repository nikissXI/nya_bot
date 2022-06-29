from tortoise import fields
from tortoise.models import Model
from tortoise.expressions import Q


class Sponsor(Model):
    qqnum = fields.IntField(pk=True)
    money = fields.IntField()
    wgnum = fields.IntField()

    ########################
    # 增加
    ########################
    # 创建信息
    @classmethod
    async def create_sponsor(cls, qqnum: int, money: int, wgnum: int):
        await cls.create(qqnum=qqnum, money=money, wgnum=wgnum)

    ########################
    # 删除
    ########################
    # 删除信息
    @classmethod
    async def delete_sponsor(cls, qqnum: int):
        await cls.filter(qqnum=qqnum).delete()

    ########################
    # 查询
    ########################
    # 获取赞助总额
    @classmethod
    async def get_money_sum(cls) -> int:
        rows = await cls.filter().values_list("money")
        smoney = 0
        for row in rows:
            smoney += row[0]
        return smoney

    # 列出所有赞助者信息
    @classmethod
    async def get_all_sponsor_info(cls) -> list:
        return (
            await cls.filter().order_by("-money").values_list("money", "qqnum", "wgnum")
        )

    # 判断是否为赞助
    @classmethod
    async def sponsor_exist(cls, qqnum: int) -> bool:
        if await cls.filter(qqnum=qqnum).limit(1).exists():
            return True
        else:
            return False

    # 判断是否赞助满20元
    @classmethod
    async def vip_exist(cls, num: int) -> bool:
        if await cls.filter(Q(money__gte=20), (Q(qqnum=num) | Q(wgnum=num))).exists():
            return True
        else:
            return False

    # 列出所有赞助满20元的信息
    @classmethod
    async def get_all_vip_info(cls) -> list:
        return await cls.filter(Q(money__gte=20), Q(wgnum__not=0)).values_list(
            "qqnum", "wgnum"
        )

    # 获取赞助者金额
    @classmethod
    async def get_money(cls, qqnum: int) -> int:
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("money")
        return row[0][0]

    ########################
    # 修改
    ########################
    # 更新金额
    @classmethod
    async def update_money(cls, qqnum: int, money: int):
        await cls.filter(qqnum=qqnum).limit(1).update(money=money)

    # 更新编号
    @classmethod
    async def update_wgnum(cls, qqnum: int, wgnum: int):
        await cls.filter(qqnum=qqnum).limit(1).update(wgnum=wgnum)

    class Meta:
        table = "sponsor"
