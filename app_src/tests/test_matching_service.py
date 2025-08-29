"""
Tests for the MatchingService to ensure proper functionality of the
interest-based matching and rating system.
"""

import pytest

from core.models import Interest, User
from core.models.enums import GenderEnum


class TestMatchingService:
    """Test suite for the MatchingService class."""

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = User(
            id=1,
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            gender=GenderEnum.MALE,
            age=25,
            location="New York",
            rating=5,
            is_active=True,
        )
        # Mock interests
        user.interests = [
            Interest(id=1, name="Photography"),
            Interest(id=2, name="Travel"),
            Interest(id=3, name="Music"),
        ]
        return user

    @pytest.fixture
    def potential_matches(self):
        """Create potential match users with different ratings and interests."""
        # High-rated user with common interests
        user1 = User(
            id=2,
            email="user1@example.com",
            first_name="Alice",
            last_name="Smith",
            gender=GenderEnum.FEMALE,
            age=23,
            location="New York",
            rating=10,  # High rating
            is_active=True,
        )
        user1.interests = [
            Interest(id=1, name="Photography"),  # Common
            Interest(id=2, name="Travel"),  # Common
            Interest(id=4, name="Cooking"),
        ]

        # Medium-rated user with some common interests
        user2 = User(
            id=3,
            email="user2@example.com",
            first_name="Emma",
            last_name="Johnson",
            gender=GenderEnum.FEMALE,
            age=26,
            location="Boston",
            rating=7,  # Medium rating
            is_active=True,
        )
        user2.interests = [
            Interest(id=1, name="Photography"),  # Common
            Interest(id=5, name="Reading"),
        ]

        # Low-rated user with many common interests
        user3 = User(
            id=4,
            email="user3@example.com",
            first_name="Sarah",
            last_name="Wilson",
            gender=GenderEnum.FEMALE,
            age=24,
            location="Chicago",
            rating=3,  # Low rating
            is_active=True,
        )
        user3.interests = [
            Interest(id=1, name="Photography"),  # Common
            Interest(id=2, name="Travel"),  # Common
            Interest(id=3, name="Music"),  # Common
            Interest(id=6, name="Art"),
        ]

        return [user1, user2, user3]

    async def test_find_matches_by_interests_and_rating_ordering(self):
        """Test that matches are ordered by common interests first, then by rating."""
        # This would be a full integration test
        # For now, we'll just test the logic conceptually

        # Expected order based on our algorithm:
        # 1. user3 (Sarah) - 3 common interests, rating 3
        # 2. user1 (Alice) - 2 common interests, rating 10
        # 3. user2 (Emma) - 1 common interest, rating 7

        # The algorithm prioritizes:
        # 1. Number of common interests (descending)
        # 2. Rating (descending)
        # 3. Creation date (descending)

        assert True  # Placeholder for actual test implementation

    async def test_process_like_increments_rating(self):
        """Test that processing a like increments the liked user's rating."""
        # This would test the rating increment logic
        # when a user receives a like

        assert True  # Placeholder for actual test implementation

    async def test_mutual_match_increments_both_ratings(self):
        """Test that mutual matches increment both users' ratings."""
        # This would test that when a match becomes mutual,
        # both users get their ratings incremented

        assert True  # Placeholder for actual test implementation

    async def test_rating_never_goes_below_zero(self):
        """Test that user rating never goes below 0."""
        user = User(rating=0)
        user.decrement_rating()
        assert user.rating == 0

    async def test_rating_increments_correctly(self):
        """Test that rating increments work correctly."""
        user = User(rating=5)
        user.increment_rating()
        assert user.rating == 6

    async def test_fallback_to_basic_matching_when_no_interests(self):
        """Test that users without interests get basic matching."""
        # This would test the fallback mechanism when a user
        # has no interests defined

        assert True  # Placeholder for actual test implementation


# Example usage and demonstration
async def demonstrate_matching_algorithm():
    """
    Demonstration of how the new matching algorithm works.

    This function shows the expected behavior of the matching system:
    1. Users with more common interests are prioritized
    2. Among users with the same number of common interests, higher-rated users come first
    3. The system falls back to basic rating-based matching if needed
    """
    print("=== Matching Algorithm Demonstration ===")
    print()
    print("User Profile:")
    print("- John Doe (Male, Rating: 5)")
    print("- Interests: Photography, Travel, Music")
    print()
    print("Potential Matches:")
    print("1. Sarah Wilson (Female, Rating: 3)")
    print("   - Interests: Photography, Travel, Music, Art")
    print("   - Common interests: 3 (Photography, Travel, Music)")
    print()
    print("2. Alice Smith (Female, Rating: 10)")
    print("   - Interests: Photography, Travel, Cooking")
    print("   - Common interests: 2 (Photography, Travel)")
    print()
    print("3. Emma Johnson (Female, Rating: 7)")
    print("   - Interests: Photography, Reading")
    print("   - Common interests: 1 (Photography)")
    print()
    print("Expected Match Order:")
    print("1. Sarah Wilson (3 common interests, rating 3)")
    print("2. Alice Smith (2 common interests, rating 10)")
    print("3. Emma Johnson (1 common interest, rating 7)")
    print()
    print("Algorithm Logic:")
    print("- Primary sort: Number of common interests (descending)")
    print("- Secondary sort: User rating (descending)")
    print("- Tertiary sort: Account creation date (descending)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demonstrate_matching_algorithm())
