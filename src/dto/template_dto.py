from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from models import MessageTemplate


class GetTemplatesByCategoryDTO(BaseModel):
    """Входные данные для получения шаблонов по категории."""

    category_id: int
    page: int = 1
    page_size: int = 5

    model_config = ConfigDict(frozen=True)


class GetTemplatesByScopeDTO(BaseModel):
    """Входные данные для получения шаблонов по области (глобальные или чат)."""

    scope: str  # "global" | "chat"
    chat_id: Optional[int] = None
    page: int = 1
    page_size: int = 5

    model_config = ConfigDict(frozen=True)


class GetTemplatesPaginatedDTO(BaseModel):
    """Входные данные для пагинированного списка шаблонов (категория / чат / глобальные)."""

    category_id: Optional[int] = None
    chat_id: Optional[int] = None
    page: int = 1
    page_size: int = 5

    model_config = ConfigDict(frozen=True)


class CreateTemplateFromContentDTO(BaseModel):
    """Входные данные для создания шаблона из контента."""

    author_username: Optional[str] = None
    content: Dict[str, Any]

    model_config = ConfigDict(frozen=True)


class TemplateDTO(BaseModel):
    id: int
    title: str
    content: str
    usage_count: int
    has_media: bool

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, template: MessageTemplate) -> "TemplateDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=template.id,
            title=template.title,
            content=template.content,
            usage_count=template.usage_count,
            has_media=bool(template.media_items),
        )


class UpdateTemplateTitleDTO(BaseModel):
    template_id: int
    new_title: str

    model_config = ConfigDict(frozen=True)


class TemplateSearchResultDTO(BaseModel):
    templates: List[TemplateDTO]
    total_count: int

    model_config = ConfigDict(frozen=True)
