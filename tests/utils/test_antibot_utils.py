"""Тесты для utils/antibot_utils.py."""

from utils.antibot_utils import decode_antibot_params, encode_antibot_params


def test_encode_antibot_params() -> None:
    """Кодирование chat_id и user_id в строку deep link."""
    result = encode_antibot_params(chat_id="-100123", user_id=456)
    assert result == "v_m100123_456"


def test_encode_antibot_params_replaces_minus() -> None:
    """Минус в chat_id заменяется на 'm'."""
    result = encode_antibot_params(chat_id="-100", user_id=1)
    assert "m" in result
    assert "-" not in result


def test_decode_antibot_params_valid() -> None:
    """Корректная строка декодируется в chat_id и user_id."""
    chat_id, user_id = decode_antibot_params("v_m100123_456")
    assert chat_id == "-100123"
    assert user_id == 456


def test_decode_antibot_params_invalid_prefix() -> None:
    """Неверный префикс — (None, None)."""
    assert decode_antibot_params("x_1_2") == (None, None)


def test_decode_antibot_params_wrong_parts_count() -> None:
    """Не три части — (None, None)."""
    assert decode_antibot_params("v_1") == (None, None)
    assert decode_antibot_params("v_1_2_3") == (None, None)


def test_decode_antibot_params_invalid_user_id() -> None:
    """user_id не число — (None, None)."""
    assert decode_antibot_params("v_m100_abc") == (None, None)


def test_encode_decode_roundtrip() -> None:
    """Кодирование и декодирование возвращают исходные значения."""
    chat_id, user_id = "-100999", 777
    encoded = encode_antibot_params(chat_id, user_id)
    decoded_chat, decoded_user = decode_antibot_params(encoded)
    assert decoded_chat == chat_id
    assert decoded_user == user_id
