from tortoise import fields
from tortoise.models import Model


class XLboard(Model):
    wgnum = fields.IntField()
    xlnum = fields.IntField()

    @classmethod
    async def get_all_info(cls) -> list:
        return await cls.filter().order_by("-xlnum").values_list("wgnum", "xlnum")

    @classmethod
    async def get_xl_info(cls, wgnum: int) -> bool:
        if await cls.filter(wgnum=wgnum).limit(1).exists():
            return True
        else:
            return False

    @classmethod
    async def create_xl_info(cls, wgnum: int, xlnum: int):
        await cls.create(wgnum=wgnum, xlnum=xlnum)

    @classmethod
    async def update_xl_info(cls, wgnum: int, xlnum: int):
        await cls.filter(wgnum=wgnum).limit(1).update(xlnum=xlnum)

    @classmethod
    async def update_wgnum(cls, wgnum: int, new_wgnum: int):
        await cls.filter(wgnum=wgnum).limit(1).update(wgnum=new_wgnum)

    @classmethod
    async def delete_xl_info(cls, wgnum: int):
        await cls.filter(wgnum=wgnum).delete()

    class Meta:
        table = "xlboard"
