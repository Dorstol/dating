# Dating App Matching System

## Overview

The matching system has been refactored to provide intelligent matching based on common interests and user ratings. This document explains the new architecture and algorithms.

## Key Features

### 1. Interest-Based Matching
- **Primary Algorithm**: Find users with common interests first
- **Intelligent Sorting**: Users with more common interests are prioritized
- **Fallback Mechanism**: If a user has no interests, falls back to basic matching

### 2. Hidden Rating System
- **Initial Rating**: Every new user starts with a rating of 0
- **Rating Increment**: Rating increases by +1 when another user likes their profile
- **Mutual Match Bonus**: Both users get +1 rating when a match becomes mutual
- **Floor Protection**: Rating never goes below 0
- **Hidden from Users**: Rating is never exposed in user-facing APIs

### 3. Smart Sorting Algorithm
The matching algorithm uses a multi-tier sorting system:

1. **Primary**: Number of common interests (descending)
2. **Secondary**: User rating (descending) 
3. **Tertiary**: Account creation date (descending)

## Architecture

### MatchingService Class
The new `MatchingService` class provides a clean, service-oriented architecture:

```python
class MatchingService:
    # Main matching algorithm
    async def find_matches_by_interests_and_rating(...)
    
    # Fallback for users without interests  
    async def _find_basic_matches(...)
    
    # Like processing with rating updates
    async def process_like(...)
    
    # Helper methods for cleaner code
    async def _get_existing_match(...)
    async def _get_user_by_id(...)
    async def _handle_existing_match(...)
    async def _create_new_match(...)
```

## Matching Algorithm Details

### Step 1: Interest-Based Matching
```sql
SELECT users.*
FROM users
JOIN user_interests ON users.id = user_interests.user_id
WHERE 
    users.gender != :user_gender
    AND users.id != :user_id
    AND users.is_active = true
    AND user_interests.interest_id IN (:user_interest_ids)
GROUP BY users.id
ORDER BY 
    COUNT(user_interests.interest_id) DESC,  -- More common interests first
    users.rating DESC,                       -- Higher rating second
    users.created_at DESC                    -- Newer users third
LIMIT :limit
```

### Step 2: Fallback Matching
If not enough matches are found with common interests:

```sql
SELECT users.*
FROM users
WHERE 
    users.gender != :user_gender
    AND users.id != :user_id
    AND users.is_active = true
    AND users.id NOT IN (:already_matched_ids)
ORDER BY 
    users.rating DESC,        -- Higher rating first
    users.created_at DESC     -- Newer users second
LIMIT :remaining_limit
```

## Rating System Logic

### Like Processing
1. **Validation**: Ensure user isn't liking themselves
2. **User Lookup**: Get the user being liked
3. **Match Check**: Look for existing matches
4. **Rating Update**: Increment liked user's rating
5. **Match Creation**: Create or update match records

### Mutual Match Handling
When a match becomes mutual:
1. Set `is_mutual = True` on existing match
2. Increment both users' ratings
3. Create reverse match record
4. Commit changes to database

## Benefits

### For Users
- **Better Matches**: Users see others with similar interests first
- **Quality Over Quantity**: Higher-rated users (more popular) are prioritized
- **Fair Distribution**: New users still get visibility through creation date sorting

### For the Platform  
- **Engagement**: Better matches lead to more user engagement
- **Retention**: Users are more likely to find compatible matches
- **Analytics**: Hidden rating system provides valuable user popularity data

## Database Schema

### User Model Updates
```python
class User(Base, IntIdPkMixin, SQLAlchemyBaseUserTable[UserIdType]):
    # ... existing fields ...
    
    rating: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    def increment_rating(self) -> None:
        """Increase user rating by 1"""
        self.rating += 1
    
    def decrement_rating(self) -> None:
        """Decrease user rating by 1, never below 0"""
        self.rating = max(0, self.rating - 1)
```

### Migration
A database migration adds the rating column with:
- Default value of 0 for all existing users
- Index on rating for efficient sorting
- Non-null constraint with server default

## Backward Compatibility

The refactoring maintains backward compatibility through:
- **Legacy Functions**: Original `find_matches()` and `process_match()` functions
- **Same Signatures**: API contracts remain unchanged
- **Gradual Migration**: New service can be adopted incrementally

## Testing

Comprehensive test suite covers:
- Interest-based matching algorithm
- Rating increment/decrement logic
- Mutual match handling
- Fallback mechanisms
- Edge cases and error handling

## Future Enhancements

Potential improvements:
1. **Geographic Matching**: Factor in location proximity
2. **Age Preferences**: Allow users to set age range preferences  
3. **Interest Weighting**: Weight certain interests more heavily
4. **Machine Learning**: Use ML to improve match quality over time
5. **Compatibility Scoring**: Develop more sophisticated compatibility algorithms

## Performance Considerations

- **Database Indexes**: Rating and interest fields are indexed for fast queries
- **Query Optimization**: Efficient JOINs and proper use of LIMIT clauses
- **Caching**: Consider caching popular user profiles
- **Pagination**: Large result sets should be paginated

---

This matching system provides a solid foundation for intelligent, engaging user matching while maintaining clean, maintainable code architecture.
