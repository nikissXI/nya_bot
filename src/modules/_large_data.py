from tortoise import fields
from tortoise.models import Model


class Large_data(Model):
    key = fields.TextField(pk=True)
    value = fields.TextField()

    @classmethod
    async def data_reset(cls):
        if not await cls.filter(key="room_time").limit(1).exists():
            await cls.create(key="host_role", value="{}")
            await cls.create(key="join_role", value="{}")
            await cls.create(key="room_time", value="{}")
            await cls.create(key="role_name", value="{}")
            await cls.create(key="room_name", value="{}")
            await cls.create(key="privacy", value="{}")
            await cls.create(key="black", value="{}")
            await cls.create(key="join_limit", value="{}")
            await cls.create(key="version_set", value="{}")

    @classmethod
    async def load_host_role(cls) -> str:
        rows = await cls.filter(key="host_role").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_host_role(cls, data: str):
        await cls.filter(key="host_role").limit(1).update(value=data)

    @classmethod
    async def load_join_role(cls) -> str:
        rows = await cls.filter(key="join_role").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_join_role(cls, data: str):
        await cls.filter(key="join_role").limit(1).update(value=data)

    @classmethod
    async def load_room_time(cls) -> str:
        rows = await cls.filter(key="room_time").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_room_play_time(cls, data: str):
        await cls.filter(key="room_time").limit(1).update(value=data)

    @classmethod
    async def load_role_tmp(cls) -> str:
        rows = await cls.filter(key="role_name").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_role_tmp(cls, data: str):
        await cls.filter(key="role_name").limit(1).update(value=data)

    @classmethod
    async def load_room_name(cls) -> str:
        rows = await cls.filter(key="room_name").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_room_name(cls, data: str):
        await cls.filter(key="room_name").limit(1).update(value=data)

    @classmethod
    async def load_privacy(cls) -> str:
        rows = await cls.filter(key="privacy").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_privacy(cls, data: str):
        await cls.filter(key="privacy").limit(1).update(value=data)

    @classmethod
    async def load_black(cls) -> str:
        rows = await cls.filter(key="black").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_black(cls, data: str):
        await cls.filter(key="black").limit(1).update(value=data)

    @classmethod
    async def load_join_limit(cls) -> str:
        rows = await cls.filter(key="join_limit").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_join_limit(cls, data: str):
        await cls.filter(key="join_limit").limit(1).update(value=data)

    @classmethod
    async def load_version_set(cls) -> str:
        rows = await cls.filter(key="version_set").limit(1).values_list("value")
        return rows[0][0]

    @classmethod
    async def save_version_set(cls, data: str):
        await cls.filter(key="version_set").limit(1).update(value=data)

    class Meta:
        table = "large_data"
