from pydantic import BaseModel, ConfigDict

from models import TemplateCategory


class CategoryDTO(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, category: TemplateCategory) -> "CategoryDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=category.id,
            name=category.name,
        )


class CreateCategoryDTO(BaseModel):
    name: str

    model_config = ConfigDict(frozen=True)


class UpdateCategoryDTO(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(frozen=True)
