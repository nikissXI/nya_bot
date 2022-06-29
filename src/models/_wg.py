from tortoise import fields
from tortoise.models import Model
from tortoise.expressions import Q


class Wg(Model):
    wgnum = fields.IntField(pk=True)
    qqnum = fields.IntField()
    ttl = fields.IntField()
    numtype = fields.TextField()
    key = fields.TextField()
    played = fields.IntField()

    ########################
    # 增加
    ########################
    # 创建新编号
    @classmethod
    async def create_wgnum(cls, wgnum: int):
        await cls.create(wgnum=wgnum, qqnum=0, ttl=0, numtype="", key="", played=0)

    ########################
    # 删除
    ########################
    # 删除编号
    @classmethod
    async def delete_wgnum(cls, wgnum: int):
        await cls.filter(wgnum=wgnum).delete()

    ########################
    # 查询
    ########################
    # 通过key获取编号信息
    @classmethod
    async def get_info_by_key(cls, key: str) -> tuple[int, int, str]:
        row = (
            await cls.filter(key=key).limit(1).values_list("wgnum", "qqnum", "numtype")
        )
        return (row[0][0], row[0][1], row[0][2])

    # 查询今日联机flag
    @classmethod
    async def get_play_flag_by_wgnum(cls, wgnum: int) -> int:
        rows = await cls.filter(wgnum=wgnum).limit(1).values_list("played")
        return rows[0][0]

    # 查询今日联机人数
    @classmethod
    async def get_players_count_today(cls) -> int:
        return await cls.filter(played=1).count()

    # 列出该类型的所有编号信息
    @classmethod
    async def get_all_info(cls, numtype: str) -> tuple[int, int, int, str]:
        return await cls.filter(numtype=numtype).values_list(
            "wgnum", "qqnum", "ttl", "numtype"
        )

    # 列出所有已绑定的编号信息
    @classmethod
    async def get_all_bind_info(cls) -> tuple[int, int, int, str, int]:
        return await cls.filter(Q(qqnum__not=0)).values_list(
            "wgnum", "qqnum", "ttl", "numtype", "played"
        )

    # 获取下载key
    @classmethod
    async def get_key_by_wgnum(cls, num: int) -> str:
        key = (
            await cls.filter(Q(wgnum=num) | Q(qqnum=num)).limit(1).values_list("key")
        )[0][0]
        return key

    # 通过qq或编号获取编号信息
    @classmethod
    async def get_info_by_wgnum(cls, num: int) -> tuple[int, int, int, str]:
        row = (
            await cls.filter(Q(wgnum=num) | Q(qqnum=num))
            .limit(1)
            .values_list("wgnum", "qqnum", "ttl", "numtype")
        )
        return (row[0][0], row[0][1], row[0][2], row[0][3])

    # 通过编号获取qq号
    @classmethod
    async def get_qq_by_wgnum(cls, wgnum: int) -> int:
        row = await cls.filter(wgnum=wgnum).limit(1).values_list("qqnum")
        if row:
            return row[0][0]
        else:
            return 0

    # 通过qq号获取编号
    @classmethod
    async def get_wgnum_by_qq(cls, qqnum: int) -> int:
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("wgnum")
        if row:
            return row[0][0]
        else:
            return 0

    # 返回编号总数
    @classmethod
    async def get_wgnum_count(cls) -> int:
        return await cls.filter().count()

    # 返回一个可用编号
    @classmethod
    async def get_a_usable_wgnum(cls) -> int:
        row = (
            await cls.filter(Q(wgnum__gte=10), Q(qqnum=0)).limit(1).values_list("wgnum")
        )
        if row:
            return row[0][0]
        else:
            return 0

    # 返回所有可用编号
    @classmethod
    async def get_all_unbind_wgnum(cls) -> list:
        rows = await cls.filter(qqnum=0).values_list("wgnum")
        return [row[0] for row in rows]

    # 返回所有非赞助编号
    @classmethod
    async def get_all_unsponsor_wgnum(cls) -> list:
        rows = await cls.filter(numtype__not="赞助").values_list("wgnum")
        return [row[0] for row in rows]

    # 该key是否存在
    @classmethod
    async def key_exist(cls, key: str) -> bool:
        return await cls.filter(key=key).limit(1).exists()

    # qq号存在或编号存在且被使用
    @classmethod
    async def num_bind(cls, num: int) -> bool:
        return (
            await cls.filter(
                Q(Q(qqnum=num), Q(qqnum__not=0)) | Q(Q(wgnum=num), Q(qqnum__not=0))
            )
            .limit(1)
            .exists()
        )

    # 判断该编号是否小于最大的且正在使用的编号
    @classmethod
    async def wgnum_in_range(cls, wgnum: int) -> bool:
        return await cls.filter(Q(wgnum__gt=wgnum), Q(qqnum__not=0)).limit(1).exists()

    ########################
    # 修改
    ########################
    # 更新ttl
    @classmethod
    async def update_ttl_by_wgnum(cls, wgnum: int, ttl: int):
        await cls.filter(wgnum=wgnum).limit(1).update(ttl=ttl)

    # 更新ttl和编号类型
    @classmethod
    async def update_ttl_and_numtype_by_wgnum(cls, wgnum: int, ttl: int, numtype: str):
        await cls.filter(wgnum=wgnum).limit(1).update(ttl=ttl, numtype=numtype)

    # 更新该编号的所有信息
    @classmethod
    async def update_info_by_wgnum(
        cls, wgnum: int, qqnum: int, ttl: int, numtype: str, played: int
    ):
        await cls.filter(wgnum=wgnum).limit(1).update(
            qqnum=qqnum, ttl=ttl, numtype=numtype, played=played
        )

    # 更新key
    @classmethod
    async def update_key_by_wgnum(cls, wgnum: int, key: str):
        await cls.filter(wgnum=wgnum).limit(1).update(key=key)

    # 重置今日联机flag
    @classmethod
    async def reset_play_flag(cls):
        await cls.filter().update(played=0)

    # 更新今日联机flag
    @classmethod
    async def update_play_flag_by_wgnum(cls, wgnum: int):
        await cls.filter(wgnum=wgnum).limit(1).update(played=1)

    class Meta:
        table = "wg_data"
