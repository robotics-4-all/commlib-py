from pydantic import BaseModel


class AuthBase(BaseModel):
    pass


class AuthPlain(AuthBase):
    username: str
    password: str


class ConnectionParametersBase(BaseModel):
    host: str
    port: int
