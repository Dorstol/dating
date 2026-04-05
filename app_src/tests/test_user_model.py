"""Unit tests for User model methods."""


class TestUserRating:
    def test_increment_rating(self, make_user):
        user = make_user(rating=5)
        user.increment_rating()
        assert user.rating == 6

    def test_increment_from_zero(self, make_user):
        user = make_user(rating=0)
        user.increment_rating()
        assert user.rating == 1

    def test_decrement_rating(self, make_user):
        user = make_user(rating=5)
        user.decrement_rating()
        assert user.rating == 4

    def test_decrement_never_below_zero(self, make_user):
        user = make_user(rating=0)
        user.decrement_rating()
        assert user.rating == 0

    def test_decrement_from_one(self, make_user):
        user = make_user(rating=1)
        user.decrement_rating()
        assert user.rating == 0

    def test_multiple_increments(self, make_user):
        user = make_user(rating=0)
        for _ in range(10):
            user.increment_rating()
        assert user.rating == 10


class TestUserInterests:
    def test_get_interests_names(self, make_user, sample_interests):
        user = make_user(interests=sample_interests)
        names = user.get_interests_names()
        assert names == ["Photography", "Travel", "Music"]

    def test_get_interests_names_empty(self, make_user):
        user = make_user(interests=[])
        assert user.get_interests_names() == []

    def test_has_interest_true(self, make_user, sample_interests):
        user = make_user(interests=sample_interests)
        assert user.has_interest("Photography") is True

    def test_has_interest_case_insensitive(self, make_user, sample_interests):
        user = make_user(interests=sample_interests)
        assert user.has_interest("photography") is True
        assert user.has_interest("PHOTOGRAPHY") is True

    def test_has_interest_false(self, make_user, sample_interests):
        user = make_user(interests=sample_interests)
        assert user.has_interest("Cooking") is False

    def test_has_interest_empty_interests(self, make_user):
        user = make_user(interests=[])
        assert user.has_interest("Photography") is False
