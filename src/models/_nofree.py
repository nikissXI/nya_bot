from tortoise import fields
from tortoise.models import Model


class Nofree(Model):
    qqnum = fields.IntField(pk=True)

    @classmethod
    async def get_all_qqnum(cls) -> list:
        rows = await cls.filter().values_list("qqnum")
        return [str(row[0]) for row in rows]

    @classmethod
    async def add_qqnum(cls, qqnum: int) -> bool:
        try:
            await cls.create(qqnum=qqnum)
            return True
        except Exception:
            return False

    @classmethod
    async def delete_qqnum(cls, qqnum: int) -> int:
        return await cls.filter(qqnum=qqnum).limit(1).delete()

    @classmethod
    async def qqnum_exist(cls, qqnum: int) -> bool:
        return await cls.filter(qqnum=qqnum).limit(1).exists()

    class Meta:
        table = "nofree"
