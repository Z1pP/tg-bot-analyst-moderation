"""Тесты для utils/template_content.py."""

from unittest.mock import MagicMock

from utils.template_content import extract_media_content_from_messages


def test_extract_media_content_from_messages_text_only() -> None:
    """Только текст — без медиа."""
    msg = MagicMock()
    msg.html_text = "Hello"
    msg.caption = None
    msg.photo = None
    msg.document = None
    msg.video = None
    msg.animation = None

    result = extract_media_content_from_messages([msg])
    assert result["text"] == "Hello"
    assert result["media_types"] == []
    assert result["media_files"] == []
    assert result["media_unique_ids"] == []


def test_extract_media_content_from_messages_caption_fallback() -> None:
    """При отсутствии html_text используется caption."""
    msg = MagicMock()
    msg.html_text = None
    msg.caption = "Caption text"
    msg.photo = None
    msg.document = None
    msg.video = None
    msg.animation = None

    result = extract_media_content_from_messages([msg])
    assert result["text"] == "Caption text"


def test_extract_media_content_from_messages_photo() -> None:
    """Фото: извлекается file_id и file_unique_id из последнего размера."""
    msg = MagicMock()
    msg.html_text = ""
    msg.caption = None
    small = MagicMock()
    small.file_id = "small_id"
    small.file_unique_id = "small_unique"
    big = MagicMock()
    big.file_id = "big_id"
    big.file_unique_id = "big_unique"
    msg.photo = [small, big]
    msg.document = None
    msg.video = None
    msg.animation = None

    result = extract_media_content_from_messages([msg])
    assert result["media_types"] == ["photo"]
    assert result["media_files"] == ["big_id"]
    assert result["media_unique_ids"] == ["big_unique"]


def test_extract_media_content_from_messages_document() -> None:
    """Документ извлекается как медиа."""
    msg = MagicMock()
    msg.html_text = ""
    msg.caption = None
    msg.photo = None
    doc = MagicMock()
    doc.file_id = "doc_id"
    doc.file_unique_id = "doc_unique"
    msg.document = doc
    msg.video = None
    msg.animation = None

    result = extract_media_content_from_messages([msg])
    assert result["media_types"] == ["document"]
    assert result["media_files"] == ["doc_id"]
    assert result["media_unique_ids"] == ["doc_unique"]


def test_extract_media_content_from_messages_multiple_messages() -> None:
    """Несколько сообщений — медиа собираются из каждого."""
    msg1 = MagicMock()
    msg1.html_text = "First"
    msg1.caption = None
    msg1.photo = None
    msg1.document = None
    msg1.video = None
    msg1.animation = None

    msg2 = MagicMock()
    msg2.html_text = ""
    msg2.caption = None
    msg2.photo = None
    msg2.document = None
    vid = MagicMock()
    vid.file_id = "vid_id"
    vid.file_unique_id = "vid_unique"
    msg2.video = vid
    msg2.animation = None

    result = extract_media_content_from_messages([msg1, msg2])
    assert result["text"] == "First"
    assert "video" in result["media_types"]
    assert "vid_id" in result["media_files"]
