from pydantic import BaseModel, Field


class ModuleBaseModel(BaseModel):
    id: str = Field(..., description="module_id")


class AddAdminModel(BaseModel):
    id: str = Field(..., description="target_user_id")


class AddModuleModel(BaseModel):
    name: str = Field(...)


class DeleteModuleModel(ModuleBaseModel):
    pass


class UpdateModuleModel(ModuleBaseModel):
    id: str = Field(..., description="module_id")
    new_name: str = Field(...)
