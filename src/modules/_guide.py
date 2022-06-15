from tortoise import fields
from tortoise.models import Model
from datetime import datetime


class Guide(Model):
    id = fields.IntField(pk=True)
    sort = fields.TextField()
    title = fields.TextField()
    author = fields.TextField()
    date = fields.TextField()
    link = fields.TextField()

    @classmethod
    async def get_guide(cls) -> list:
        rows = (
            await cls.filter()
            .order_by("-id")
            .values_list("id", "sort", "title", "author", "date", "link")
        )
        return rows

    @classmethod
    async def create_guide(cls, sort: str, title: str, author: str, link: str) -> list:
        date = datetime.now().strftime("%Y-%m-%d")
        return await cls.create(sort=sort, title=title, author=author, date=date, link=link)

    @classmethod
    async def delete_guide(cls, id: int) -> int:
        return await cls.filter(id=id).limit(1).delete()

    class Meta:
        table = "guide"
