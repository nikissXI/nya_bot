from tortoise import fields
from tortoise.models import Model
from hashlib import md5


class Zhb_user(Model):
    qqnum = fields.IntField(pk=True)
    username = fields.TextField()
    password = fields.TextField()

    @classmethod
    async def qq_exist(cls, qqnum: int) -> bool:
        return await cls.filter(qqnum=qqnum).limit(1).exists()

    @classmethod
    async def get_nick_by_pass(cls, password: str) -> str:
        row = await cls.filter(password=password).limit(1).values_list("username")
        if row:
            return row[0][0]
        else:
            return None

    @classmethod
    async def get_nick_by_qq(cls, qqnum: int) -> str:
        row = await cls.filter(qqnum=qqnum).limit(1).values_list("username")
        if row:
            return row[0][0]
        else:
            return None

    @classmethod
    async def get_all_user(cls) -> str:
        rows = await cls.filter().values_list("qqnum", "username", "password")
        user_list = [
            f"Q号: {row[0]}&emsp;&emsp;&emsp;昵称: {row[1]}<br />key: {row[2]}"
            for row in rows
        ]
        return "<br /><br />".join(user_list)

    @classmethod
    async def create_user(cls, qqnum: int, username: str) -> str:
        if await cls.filter(qqnum=qqnum).limit(1).exists():
            return f"{qqnum}已创建账号"
        else:
            m = md5(str(qqnum).encode("utf8")).hexdigest()
            m = md5(m.encode("utf8")).hexdigest()
            m = md5(m.encode("utf8")).hexdigest()
            await cls.create(qqnum=qqnum, username=username, password=m)
            return f"创建成功!<br />Q号: {qqnum}<br />昵称: {username}<br />key: {m}"

    @classmethod
    async def delete_user(cls, qqnum: int) -> str:
        if await cls.filter(qqnum=qqnum).limit(1).exists():
            await cls.filter(qqnum=qqnum).limit(1).delete()
            return f"删除{qqnum}成功"
        else:
            return f"{qqnum}不存在"

    class Meta:
        table = "zhb_user"
