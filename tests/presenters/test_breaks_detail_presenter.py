"""Тесты для BreaksDetailPresenter."""

from dto.report import (
    BreaksDetailReportDTO,
    BreaksDetailUserDTO,
)
from presenters.breaks_detail_presenter import BreaksDetailPresenter


def test_format_report_error_message_returns_error_in_list() -> None:
    """При error_message возвращается список из одного элемента с текстом ошибки."""
    result = BreaksDetailPresenter.format_report(
        BreaksDetailReportDTO(
            period="01.01.2025",
            users=[],
            error_message="Ошибка загрузки",
        )
    )
    assert result == ["Ошибка загрузки"]


def test_format_report_no_users_returns_no_data_message() -> None:
    """При пустом списке users возвращается сообщение об отсутствии данных."""
    result = BreaksDetailPresenter.format_report(
        BreaksDetailReportDTO(period="01.01.2025", users=[], error_message=None)
    )
    assert len(result) == 1
    assert "Нет данных" in result[0] or "детализац" in result[0].lower()


def test_format_report_with_user_no_activity_returns_header_and_pause() -> None:
    """При пользователе без активности возвращается заголовок и «Перерывы отсутствуют»."""
    user = BreaksDetailUserDTO(
        username="user",
        has_activity=False,
        days=[],
    )
    result = BreaksDetailPresenter.format_report(
        BreaksDetailReportDTO(period="01.01.2025", users=[user], error_message=None)
    )
    assert len(result) >= 1
    assert "@user" in result[0]
    assert "Перерывы отсутствуют" in result[0]
