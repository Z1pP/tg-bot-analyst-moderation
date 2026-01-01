from typing import List

from pydantic import BaseModel, ConfigDict

from models import MessageTemplate


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
