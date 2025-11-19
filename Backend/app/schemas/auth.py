from pydantic import BaseModel


class Credenciales(BaseModel):
    nombre: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    usuario: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str
