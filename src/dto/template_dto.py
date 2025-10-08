from dataclasses import dataclass
from typing import List

from models import MessageTemplate


@dataclass(frozen=True)
class TemplateDTO:
    id: int
    title: str
    content: str
    usage_count: int
    has_media: bool

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


@dataclass(frozen=True)
class UpdateTemplateTitleDTO:
    template_id: int
    new_title: str


@dataclass(frozen=True)
class TemplateSearchResultDTO:
    templates: List[TemplateDTO]
    total_count: int
