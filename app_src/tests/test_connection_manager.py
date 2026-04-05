"""Unit tests for ConnectionManager."""

import json
from unittest.mock import AsyncMock, patch


from crud.services.connection_manager import ConnectionManager


class TestConnect:
    async def test_accepts_websocket_and_registers(self):
        cm = ConnectionManager()
        ws = AsyncMock()

        with patch.object(cm, "_get_redis", new_callable=AsyncMock) as mock_redis:
            mock_r = AsyncMock()
            mock_redis.return_value = mock_r
            cm._pubsub = AsyncMock()
            cm._pubsub.subscribe = AsyncMock()

            await cm.connect(ws, match_id=1, user_id=10)

        ws.accept.assert_awaited_once()
        assert 1 in cm._connections
        assert cm._connections[1][10] is ws

    async def test_multiple_users_same_match(self):
        cm = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        with patch.object(cm, "_get_redis", new_callable=AsyncMock):
            cm._pubsub = AsyncMock()
            cm._pubsub.subscribe = AsyncMock()

            await cm.connect(ws1, match_id=1, user_id=10)
            await cm.connect(ws2, match_id=1, user_id=20)

        assert cm._connections[1][10] is ws1
        assert cm._connections[1][20] is ws2


class TestDisconnect:
    async def test_removes_user_connection(self):
        cm = ConnectionManager()
        cm._connections = {1: {10: AsyncMock(), 20: AsyncMock()}}

        await cm.disconnect(1, 10)

        assert 10 not in cm._connections[1]
        assert 20 in cm._connections[1]

    async def test_removes_match_when_empty(self):
        cm = ConnectionManager()
        cm._connections = {1: {10: AsyncMock()}}
        cm._pubsub = AsyncMock()

        await cm.disconnect(1, 10)

        assert 1 not in cm._connections

    async def test_noop_for_unknown_match(self):
        cm = ConnectionManager()
        cm._connections = {}

        await cm.disconnect(999, 10)  # Should not raise


class TestDeliverLocal:
    async def test_delivers_to_all_except_excluded(self):
        cm = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        cm._connections = {1: {10: ws1, 20: ws2}}

        msg = {"text": "hello"}
        await cm._deliver_local(1, msg, exclude_user_id=10)

        ws1.send_json.assert_not_awaited()
        ws2.send_json.assert_awaited_once_with(msg)

    async def test_delivers_to_all_when_no_exclusion(self):
        cm = ConnectionManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        cm._connections = {1: {10: ws1, 20: ws2}}

        msg = {"text": "hello"}
        await cm._deliver_local(1, msg)

        ws1.send_json.assert_awaited_once_with(msg)
        ws2.send_json.assert_awaited_once_with(msg)

    async def test_disconnects_on_send_error(self):
        cm = ConnectionManager()
        ws = AsyncMock()
        ws.send_json.side_effect = Exception("connection closed")
        cm._connections = {1: {10: ws}}

        await cm._deliver_local(1, {"text": "hi"})

        assert 1 not in cm._connections


class TestBroadcast:
    async def test_publishes_to_redis(self):
        cm = ConnectionManager()
        mock_r = AsyncMock()
        cm._redis = mock_r

        msg = {"text": "hello", "sender_id": 10}
        await cm.broadcast(1, msg)

        mock_r.publish.assert_awaited_once_with("chat:1", json.dumps(msg))

    async def test_falls_back_to_local_on_redis_error(self):
        import redis

        cm = ConnectionManager()
        mock_r = AsyncMock()
        mock_r.publish.side_effect = redis.RedisError("down")
        cm._redis = mock_r

        ws = AsyncMock()
        cm._connections = {1: {20: ws}}

        msg = {"text": "hello", "sender_id": 10}
        await cm.broadcast(1, msg, exclude_user_id=10)

        ws.send_json.assert_awaited_once_with(msg)


class TestClose:
    async def test_cleanup_resources(self):
        cm = ConnectionManager()
        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        cm._redis = mock_redis
        cm._pubsub = mock_pubsub

        await cm.close()

        mock_redis.close.assert_awaited_once()
        mock_pubsub.close.assert_awaited_once()
        assert cm._redis is None
        assert cm._pubsub is None
