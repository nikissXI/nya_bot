from tortoise import fields
from tortoise.models import Model


class Shencha(Model):
    qqnum = fields.IntField(pk=True)
    mess = fields.TextField()

    @classmethod
    async def get_all(cls) -> list:
        rows = await cls.filter().values_list("mess")
        if rows:
            return [f"\n{row[0]}" for row in rows]
        else:
            return "  空"

    @classmethod
    async def get_one(cls, qqnum: int) -> str:
        rows = await cls.filter(qqnum=qqnum).limit(1).values_list("mess")
        return rows[0][0]

    @classmethod
    async def add_qqnum(cls, qqnum: int, mess: str):
        if await cls.qqnum_exist(qqnum):
            await cls.delete_qqnum(qqnum)
        await cls.create(qqnum=qqnum, mess=mess)

    @classmethod
    async def delete_qqnum(cls, qqnum: int) -> int:
        return await cls.filter(qqnum=qqnum).limit(1).delete()

    @classmethod
    async def qqnum_exist(cls, qqnum: int) -> bool:
        return await cls.filter(qqnum=qqnum).limit(1).exists()

    class Meta:
        table = "shencha"
