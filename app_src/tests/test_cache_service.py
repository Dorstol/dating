"""Unit tests for CacheService."""

from unittest.mock import AsyncMock, patch

import pytest

from crud.services.cache_service import CacheService


class TestCacheService:
    @pytest.fixture(autouse=True)
    def reset_redis(self):
        CacheService._redis = None
        yield
        CacheService._redis = None

    @pytest.fixture
    def mock_redis(self):
        return AsyncMock()

    async def test_get_json_returns_cached_data(self, mock_redis):
        mock_redis.get.return_value = '{"items": [1, 2, 3]}'
        CacheService._redis = mock_redis

        result = await CacheService.get_json("suggestions", 1, 20, 0)

        assert result == {"items": [1, 2, 3]}
        mock_redis.get.assert_awaited_once_with("dating:suggestions:1:20:0")

    async def test_get_json_returns_none_on_miss(self, mock_redis):
        mock_redis.get.return_value = None
        CacheService._redis = mock_redis

        result = await CacheService.get_json("suggestions", 1, 20, 0)

        assert result is None

    async def test_get_json_returns_none_on_redis_error(self, mock_redis):
        import redis.asyncio as redis

        mock_redis.get.side_effect = redis.RedisError("connection refused")
        CacheService._redis = mock_redis

        result = await CacheService.get_json("suggestions", 1, 20, 0)

        assert result is None

    async def test_set_json_stores_data_with_ttl(self, mock_redis):
        CacheService._redis = mock_redis

        await CacheService.set_json(
            {"items": []}, "suggestions", 1, 20, 0, ttl=300
        )

        mock_redis.set.assert_awaited_once_with(
            "dating:suggestions:1:20:0",
            '{"items": []}',
            ex=300,
        )

    async def test_set_json_silent_on_redis_error(self, mock_redis):
        import redis.asyncio as redis

        mock_redis.set.side_effect = redis.RedisError("connection refused")
        CacheService._redis = mock_redis

        # Should not raise
        await CacheService.set_json({"items": []}, "suggestions", 1, ttl=60)

    async def test_delete_pattern_scans_and_deletes(self, mock_redis):
        mock_redis.scan.return_value = (
            0,
            ["dating:suggestions:1:20:0", "dating:suggestions:1:20:20"],
        )
        CacheService._redis = mock_redis

        await CacheService.delete_pattern("suggestions", 1, "")

        mock_redis.scan.assert_awaited_once()
        mock_redis.delete.assert_awaited_once_with(
            "dating:suggestions:1:20:0", "dating:suggestions:1:20:20"
        )

    async def test_delete_pattern_handles_empty_result(self, mock_redis):
        mock_redis.scan.return_value = (0, [])
        CacheService._redis = mock_redis

        await CacheService.delete_pattern("suggestions", 1, "")

        mock_redis.delete.assert_not_awaited()

    async def test_invalidate_suggestions_delegates_to_delete_pattern(
        self, mock_redis
    ):
        mock_redis.scan.return_value = (0, [])
        CacheService._redis = mock_redis

        with patch.object(CacheService, "delete_pattern") as mock_delete:
            await CacheService.invalidate_suggestions(42)
            mock_delete.assert_awaited_once_with("suggestions", 42, "")

    async def test_make_key_builds_correct_format(self):
        key = CacheService._make_key("suggestions", 1, 20, 0)
        assert key == "dating:suggestions:1:20:0"

    async def test_close_resets_connection(self, mock_redis):
        CacheService._redis = mock_redis

        await CacheService.close()

        mock_redis.close.assert_awaited_once()
        assert CacheService._redis is None

    async def test_close_noop_when_no_connection(self):
        CacheService._redis = None
        await CacheService.close()  # Should not raise
