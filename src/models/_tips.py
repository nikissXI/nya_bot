from tortoise import fields
from tortoise.models import Model


class Tips(Model):
    id = fields.IntField(pk=True)
    tip = fields.TextField()

    @classmethod
    async def get_all_tip(cls) -> list:
        return await cls.filter().order_by("id").values_list("id", "tip")

    @classmethod
    async def create_tip(cls, tip: str) -> int:
        rows = await cls.get_all_tip()
        ids = [row[0] for row in rows]
        id = 1
        while True:
            if id in ids:
                id += 1
            else:
                break
        await cls.create(id=id, tip=tip)
        return id

    @classmethod
    async def delete_tip(cls, id: int):
        await cls.filter(id=id).delete()

    class Meta:
        table = "tips"
