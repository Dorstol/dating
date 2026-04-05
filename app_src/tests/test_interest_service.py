"""Unit tests for InterestService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.models import Interest, User
from crud.services.interest_service import InterestService


class TestGetOrCreateInterests:
    @pytest.fixture
    def session(self):
        return AsyncMock()

    def _mock_existing(self, session, interests):
        """Configure session to return given interests as existing."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = interests
        session.execute.return_value = mock_result

    async def test_empty_list_returns_empty(self, session):
        result = await InterestService.get_or_create_interests(session, [])
        assert result == []
        session.execute.assert_not_awaited()

    async def test_whitespace_only_returns_empty(self, session):
        result = await InterestService.get_or_create_interests(session, ["  ", ""])
        assert result == []

    async def test_returns_existing_interests(self, session):
        existing = [Interest(id=1, name="music")]
        self._mock_existing(session, existing)

        result = await InterestService.get_or_create_interests(session, ["music"])
        assert len(result) == 1
        assert result[0].name == "music"

    async def test_creates_new_interest(self, session):
        self._mock_existing(session, [])
        session.add = MagicMock()

        result = await InterestService.get_or_create_interests(session, ["photography"])
        assert len(result) == 1
        session.add.assert_called_once()
        session.flush.assert_awaited_once()

    async def test_mixed_existing_and_new(self, session):
        existing = [Interest(id=1, name="music")]
        self._mock_existing(session, existing)
        session.add = MagicMock()

        result = await InterestService.get_or_create_interests(
            session, ["music", "cooking"]
        )
        assert len(result) == 2
        session.add.assert_called_once()

    async def test_deduplicates_within_batch(self, session):
        self._mock_existing(session, [])
        session.add = MagicMock()

        await InterestService.get_or_create_interests(session, ["Music", "music"])
        # Only one should be created despite different cases
        assert session.add.call_count == 1

    async def test_normalizes_names(self, session):
        self._mock_existing(session, [])
        session.add = MagicMock()

        await InterestService.get_or_create_interests(session, ["  Photography  "])
        added_interest = session.add.call_args[0][0]
        assert added_interest.name == "Photography"  # stripped but preserves case


class TestUpdateUserInterests:
    async def test_updates_user_interests(self):
        session = AsyncMock()
        session.add = MagicMock()

        user = User(
            id=1,
            email="a@b.com",
            hashed_password="x",
            first_name="A",
            last_name="B",
            location="NYC",
            age=25,
        )
        user.interests = []

        existing = [Interest(id=1, name="music")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = existing
        session.execute.return_value = mock_result

        result = await InterestService.update_user_interests(session, user, ["music"])
        assert result == existing
        assert user.interests == existing
        session.commit.assert_awaited_once()
