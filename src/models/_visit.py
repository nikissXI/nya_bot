from tortoise import fields
from tortoise.models import Model


class Visit(Model):
    ip = fields.TextField(pk=True)

    @classmethod
    async def ip_exist(cls, ip: str) -> bool:
        return await cls.filter(ip=ip).limit(1).exists()

    @classmethod
    async def create_ip(cls, ip: str):
        await cls.create(ip=ip)

    @classmethod
    async def clear_ip(cls):
        await cls.filter().delete()

    class Meta:
        table = "visit"
