from pydantic import BaseModel, Field


class AddAdminModel(BaseModel):
    target_user_id: str = Field(...)


class RemoveAdminModel(BaseModel):
    target_user_id: str = Field(...)


class AddModuleModel(BaseModel):
    name: str = Field(...)


class DeleteModuleModel(BaseModel):
    module_id: str = Field(...)


class UpdateModuleModel(BaseModel):
    module_id: str = Field(...)
    new_name: str = Field(...)
