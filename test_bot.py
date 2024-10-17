import pytest
import aiohttp
import aiosqlite
from bot import get_new_requests, send_request_to_telegram, save_request_to_db, is_request_sent

# Mock данные для тестирования
mock_request = {
    "id": 1,
    "name": "Иван Иванов",
    "contact": "ivan@example.com",
    "text": "Тестовая заявка",
    "datetime": "2023-10-01 12:00:00"
}

# Mock данные для некорректной заявки
mock_incorrect_request = {
    "contact": "ivan@example.com",
    "text": "Тестовая заявка",
    "datetime": "2023-10-01 12:00:00"
}

@pytest.mark.asyncio
async def test_get_new_requests(monkeypatch):
    # Mock для aiohttp.ClientSession.get
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status):
                self._json = json_data
                self.status = status

            async def json(self):
                return self._json

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def __aenter__(self):
                return self

        return MockResponse([mock_request], 200)

    monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)

    requests = await get_new_requests()
    assert len(requests) == 1
    assert requests[0] == mock_request

@pytest.mark.asyncio
async def test_get_new_requests_error(monkeypatch):
    # Mock для aiohttp.ClientSession.get с ошибкой
    async def mock_get(*args, **kwargs):
        raise aiohttp.ClientError("Test error")

    monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)

    requests = await get_new_requests()
    assert len(requests) == 0

@pytest.mark.asyncio
async def test_get_new_requests_incorrect_data(monkeypatch):
    # Mock для aiohttp.ClientSession.get с некорректными данными
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status):
                self._json = json_data
                self.status = status

            async def json(self):
                return self._json

            async def __aexit__(self, exc_type, exc, tb):
                pass

            async def __aenter__(self):
                return self

        return MockResponse([mock_incorrect_request], 200)

    monkeypatch.setattr(aiohttp.ClientSession, "get", mock_get)

    requests = await get_new_requests()
    assert len(requests) == 1
    assert requests[0] == mock_incorrect_request

@pytest.mark.asyncio
async def test_send_request_to_telegram(monkeypatch):
    # Mock для bot.send_message
    async def mock_send_message(*args, **kwargs):
        return True

    monkeypatch.setattr("bot.bot.send_message", mock_send_message)

    await send_request_to_telegram(mock_request)
    # Здесь можно добавить проверку логов или других индикаторов успешного выполнения

@pytest.mark.asyncio
async def test_send_request_to_telegram_error(monkeypatch):
    # Mock для bot.send_message с ошибкой
    async def mock_send_message(*args, **kwargs):
        raise Exception("Test error")

    monkeypatch.setattr("bot.bot.send_message", mock_send_message)

    await send_request_to_telegram(mock_request)
    # Здесь можно добавить проверку логов или других индикаторов ошибки

@pytest.mark.asyncio
async def test_send_request_to_telegram_incorrect_data(monkeypatch):
    # Mock для bot.send_message
    async def mock_send_message(*args, **kwargs):
        return True

    monkeypatch.setattr("bot.bot.send_message", mock_send_message)

    with pytest.raises(KeyError):
        await send_request_to_telegram(mock_incorrect_request)

@pytest.mark.asyncio
async def test_save_request_to_db():
    await save_request_to_db(mock_request)
    async with aiosqlite.connect('requests.db') as db:
        cursor = await db.execute('SELECT * FROM requests WHERE id = ?', (mock_request['id'],))
        row = await cursor.fetchone()
        assert row is not None

@pytest.mark.asyncio
async def test_is_request_sent():
    await save_request_to_db(mock_request)
    result = await is_request_sent(mock_request['id'])
    assert result is True

@pytest.mark.asyncio
async def test_is_request_not_sent():
    result = await is_request_sent(999)  # Несуществующий ID
    assert result is False