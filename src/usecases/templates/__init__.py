from .create_template_from_content import CreateTemplateFromContentUseCase
from .delete_template import DeleteTemplateUseCase
from .get_template_by_id import GetTemplateByIdUseCase
from .get_template_and_increase_usage import GetTemplateAndIncreaseUsageUseCase
from .get_templates_by_category import GetTemplatesByCategoryUseCase
from .get_templates_by_scope import GetTemplatesByScopeUseCase
from .get_templates_by_query import GetTemplatesByQueryUseCase
from .get_templates_paginated import GetTemplatesPaginatedUseCase
from .update_template_content import UpdateTemplateContentUseCase
from .update_template_title import UpdateTemplateTitleUseCase

__all__ = [
    "CreateTemplateFromContentUseCase",
    "DeleteTemplateUseCase",
    "GetTemplateByIdUseCase",
    "GetTemplateAndIncreaseUsageUseCase",
    "GetTemplatesByCategoryUseCase",
    "GetTemplatesByScopeUseCase",
    "GetTemplatesByQueryUseCase",
    "GetTemplatesPaginatedUseCase",
    "UpdateTemplateContentUseCase",
    "UpdateTemplateTitleUseCase",
]
