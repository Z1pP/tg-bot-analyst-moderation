from dataclasses import dataclass

from models import TemplateCategory


@dataclass(frozen=True)
class CategoryDTO:
    id: int
    name: str

    @classmethod
    def from_model(cls, category: TemplateCategory) -> "CategoryDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=category.id,
            name=category.name,
        )


@dataclass(frozen=True)
class CreateCategoryDTO:
    name: str


@dataclass(frozen=True)
class UpdateCategoryDTO:
    id: int
    name: str
