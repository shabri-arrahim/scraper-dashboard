from pydantic import BaseModel


class ScriptBase(BaseModel):
    name: str


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    name: str
    log_file: str


class ScriptResponse(ScriptBase):
    id: int
    log_file: str

    class Config:
        from_attributes = True
