from pydantic import BaseModel, Field


class AddAdminModel(BaseModel):
    id: str = Field(..., description="target_user_id")


class AddModuleModel(BaseModel):
    name: str = Field(...)


class DeleteModuleModel(BaseModel):
    id: str = Field(..., description="module_id")


class UpdateModuleModel(BaseModel):
    id: str = Field(..., description="module_id")
    new_name: str = Field(...)
