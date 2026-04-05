"""Unit tests for MatchingService business logic."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.models import Match, User
from core.models.enums import GenderEnum

# Avoid circular import: matches_service imports from api.api_v1.fastapi_users
# which triggers the full API router chain. Mock it before importing.
sys.modules.setdefault("api.api_v1.fastapi_users", MagicMock())

from crud.services.block_report_service import BlockReportService  # noqa: E402
from crud.services.cache_service import CacheService  # noqa: E402
from crud.services.matches_service import MatchingService  # noqa: E402


class TestProcessLike:
    @pytest.fixture
    def session(self):
        s = AsyncMock()
        s.add = MagicMock()
        return s

    @pytest.fixture
    def user(self, make_user):
        return make_user(
            id=1,
            email="john@example.com",
            gender=GenderEnum.MALE,
            rating=5,
        )

    @pytest.fixture
    def other_user(self, make_user):
        return make_user(
            id=2,
            email="alice@example.com",
            gender=GenderEnum.FEMALE,
            rating=3,
        )

    async def test_cannot_like_yourself(self, session, user):
        with pytest.raises(ValueError, match="Cannot match with yourself"):
            await MatchingService.process_like(session, user, user.id)

    async def test_new_like_creates_match(self, session, user, other_user):
        with (
            patch.object(
                BlockReportService,
                "get_blocked_user_ids",
                return_value=[],
            ),
            patch.object(
                MatchingService,
                "_get_user_by_id",
                return_value=other_user,
            ),
            patch.object(
                MatchingService,
                "_get_existing_match",
                return_value=None,
            ),
            patch.object(
                CacheService,
                "invalidate_suggestions",
                new_callable=AsyncMock,
            ),
        ):
            result = await MatchingService.process_like(session, user, other_user.id)

        assert result.user_id == user.id
        assert result.matched_user_id == other_user.id
        assert result.is_mutual is False
        assert other_user.rating == 4  # incremented from 3
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    async def test_mutual_like_sets_mutual_flag(self, session, user, other_user):
        existing = Match(
            user_id=other_user.id,
            matched_user_id=user.id,
            is_mutual=False,
        )

        with (
            patch.object(
                BlockReportService,
                "get_blocked_user_ids",
                return_value=[],
            ),
            patch.object(
                MatchingService,
                "_get_user_by_id",
                return_value=other_user,
            ),
            patch.object(
                MatchingService,
                "_get_existing_match",
                return_value=existing,
            ),
            patch.object(
                CacheService,
                "invalidate_suggestions",
                new_callable=AsyncMock,
            ),
        ):
            result = await MatchingService.process_like(session, user, other_user.id)

        assert existing.is_mutual is True
        assert result.is_mutual is True
        assert user.rating == 6  # incremented from 5
        assert other_user.rating == 4  # incremented from 3

    async def test_duplicate_like_returns_existing(self, session, user, other_user):
        existing = Match(
            user_id=user.id,
            matched_user_id=other_user.id,
            is_mutual=False,
        )

        with (
            patch.object(
                BlockReportService,
                "get_blocked_user_ids",
                return_value=[],
            ),
            patch.object(
                MatchingService,
                "_get_user_by_id",
                return_value=other_user,
            ),
            patch.object(
                MatchingService,
                "_get_existing_match",
                return_value=existing,
            ),
        ):
            result = await MatchingService.process_like(session, user, other_user.id)

        assert result is existing
        assert user.rating == 5  # unchanged
        assert other_user.rating == 3  # unchanged

    async def test_like_nonexistent_user_raises(self, session, user):
        with (
            patch.object(
                BlockReportService,
                "get_blocked_user_ids",
                return_value=[],
            ),
            patch.object(
                MatchingService,
                "_get_user_by_id",
                side_effect=ValueError("User with ID 999 not found"),
            ),
        ):
            with pytest.raises(ValueError, match="not found"):
                await MatchingService.process_like(session, user, 999)

    async def test_new_like_increments_only_matched_user_rating(
        self, session, user, other_user
    ):
        initial_user_rating = user.rating
        initial_other_rating = other_user.rating

        with (
            patch.object(
                BlockReportService,
                "get_blocked_user_ids",
                return_value=[],
            ),
            patch.object(
                MatchingService,
                "_get_user_by_id",
                return_value=other_user,
            ),
            patch.object(
                MatchingService,
                "_get_existing_match",
                return_value=None,
            ),
            patch.object(
                CacheService,
                "invalidate_suggestions",
                new_callable=AsyncMock,
            ),
        ):
            await MatchingService.process_like(session, user, other_user.id)

        assert user.rating == initial_user_rating  # unchanged
        assert other_user.rating == initial_other_rating + 1


class TestGetExistingMatch:
    async def test_finds_match_either_direction(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = Match(
            user_id=1, matched_user_id=2, is_mutual=False
        )
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        result = await MatchingService._get_existing_match(session, 1, 2)
        assert result is not None
        session.execute.assert_awaited_once()

    async def test_returns_none_when_no_match(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result.scalars.return_value = mock_scalars
        session.execute.return_value = mock_result

        result = await MatchingService._get_existing_match(session, 1, 2)
        assert result is None


class TestGetUserById:
    async def test_returns_user_when_found(self):
        session = AsyncMock()
        user = User(id=1, email="a@b.com", hashed_password="x")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        session.execute.return_value = mock_result

        result = await MatchingService._get_user_by_id(session, 1)
        assert result is user

    async def test_raises_when_not_found(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            await MatchingService._get_user_by_id(session, 999)
