from tortoise import fields
from tortoise.models import Model


class Little_data(Model):
    key = fields.TextField(pk=True)
    value = fields.IntField()

    @classmethod
    async def data_reset(cls):
        if not await cls.filter(key="web_visit_count").limit(1).exists():
            await cls.create(key="web_visit_count", value=15151)
            await cls.create(key="play_count_yestoday", value=273)
            await cls.create(key="play_count_today", value=66)
            await cls.create(key="miaobi_system", value=1)
            await cls.create(key="safe_mode", value=0)

    @classmethod
    async def get_miaobi_system(cls) -> bool:
        rows = await cls.filter(key="miaobi_system").limit(1).values_list("value")
        if rows[0][0]:
            return True
        else:
            return False

    @classmethod
    async def update_miaobi_system(cls, v: int) -> bool:
        await cls.filter(key="miaobi_system").limit(1).update(value=v)
        if v:
            return True
        else:
            return False

    @classmethod
    async def get_safe_mode(cls) -> bool:
        rows = await cls.filter(key="safe_mode").limit(1).values_list("value")
        if rows[0][0]:
            return True
        else:
            return False

    @classmethod
    async def update_safe_mode(cls, v: int) -> bool:
        await cls.filter(key="safe_mode").limit(1).update(value=v)
        if v:
            return True
        else:
            return False

    @classmethod
    async def get_web_visit_count(cls) -> int:
        rows = await cls.filter(key="web_visit_count").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def update_web_visit_count(cls):
        c = await cls.get_web_visit_count()
        await cls.filter(key="web_visit_count").limit(1).update(value=c + 1)

    @classmethod
    async def update_play_count_daily(cls):
        c = await cls.get_play_count_today()
        await cls.filter(key="play_count_yestoday").limit(1).update(value=c)
        await cls.filter(key="play_count_today").limit(1).update(value=0)

    @classmethod
    async def get_play_count_yestoday(cls) -> int:
        rows = await cls.filter(key="play_count_yestoday").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def get_play_count_today(cls) -> int:
        rows = await cls.filter(key="play_count_today").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def update_play_count_today(cls):
        c = await cls.get_play_count_today()
        await cls.filter(key="play_count_today").limit(1).update(value=c + 1)

    class Meta:
        table = "little_data"
