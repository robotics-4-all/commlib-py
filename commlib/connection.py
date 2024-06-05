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
    reconnect_attempts: int = 5
    reconnect_delay: float = 5.0
