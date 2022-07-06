from tortoise import fields
from tortoise.models import Model
from datetime import datetime
from ujson import loads


class Zhb_list(Model):
    qqnum = fields.IntField(pk=True)
    date = fields.TextField()
    author = fields.TextField()
    why = fields.TextField()
    path = fields.TextField()

    @classmethod
    async def get_all_info(cls, qqnum=None) -> list:
        if qqnum is None:
            rows = (
                await cls.filter()
                .order_by("-date")
                .values_list("date", "qqnum", "author")
            )
        else:
            rows = (
                await cls.filter(qqnum__contains=qqnum)
                .order_by("-date")
                .values_list("date", "qqnum", "author")
            )
        return rows

    @classmethod
    async def get_qq_list(cls) -> list:
        rows = await cls.filter().values_list("qqnum")
        qqnum_list = [row[0] for row in rows]
        return qqnum_list

    @classmethod
    async def qq_exist(cls, qqnum: int) -> bool:
        return await cls.filter(qqnum=qqnum).limit(1).exists()

    @classmethod
    async def get_why(cls, qqnum: int) -> tuple[int, str, str, list]:
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("date", "why", "path")
        return (qqnum, row[0][0], row[0][1], loads(row[0][2]))

    @classmethod
    async def create_info(cls, qqnum: int, author: str, why: str, path: str):
        date = datetime.now().strftime("%Y-%m-%d")
        await cls.create(qqnum=qqnum, date=date, author=author, why=why, path=path)

    @classmethod
    async def delete_info(cls, qqnum: int) -> bool:
        if await cls.qq_exist(qqnum):
            await cls.filter(qqnum=qqnum).limit(1).delete()
            return True
        else:
            return False

    class Meta:
        table = "zhb_list"
