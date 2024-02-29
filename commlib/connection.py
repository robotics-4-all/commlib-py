from pydantic import BaseModel


class AuthBase(BaseModel):
    pass


class AuthPlain(AuthBase):
    username: str
    password: str


class BaseConnectionParameters(BaseModel):
    host: str
    port: int
    ssl: bool = False
    ssl_insecure: bool = False
    reconnect: bool = False
    reconnect_wait: int = 5
