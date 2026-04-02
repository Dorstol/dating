"""Generate test users, interests, and mutual matches."""

import asyncio
import random

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql+asyncpg://user:password@localhost:5432/dating"

FIRST_NAMES_M = ["Alex", "Max", "Ivan", "Dmitry", "Artem", "Nikita", "Sergey", "Andrey", "Pavel", "Roman"]
FIRST_NAMES_F = ["Anna", "Maria", "Olga", "Elena", "Kate", "Sofia", "Daria", "Alina", "Yana", "Polina"]
LAST_NAMES = ["Ivanov", "Petrov", "Sidorov", "Kozlov", "Novikov", "Morozov", "Volkov", "Sokolov", "Popov", "Lebedev"]
LOCATIONS = ["Kyiv", "Lviv", "Odesa", "Kharkiv", "Dnipro"]
BIOS = [
    "Love hiking and coffee",
    "Music is my life",
    "Looking for someone to explore the city with",
    "Dog lover, foodie, traveler",
    "Just here to meet cool people",
    "Into sports and healthy lifestyle",
    "Movie buff and bookworm",
    "Adventure seeker",
    None,
    None,
]
INTEREST_NAMES = [
    "music", "travel", "cooking", "photography", "hiking",
    "movies", "reading", "gaming", "fitness", "art",
    "dancing", "yoga", "coffee", "dogs", "cats",
]

PASSWORD_HASH = "$argon2id$v=19$m=65536,t=3,p=4$dGVzdHNlZWQ$K1v2N3pR4xD5sY6ARz7B/IF8KKrmy9HK0CEg1V2U311PU"


async def seed(n_users: int = 20, n_matches: int = 5):
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as s:
        # Clean existing data
        await s.execute(text("DELETE FROM messages"))
        await s.execute(text("DELETE FROM matchs"))
        await s.execute(text("DELETE FROM user_interests"))
        await s.execute(text("DELETE FROM blocks"))
        await s.execute(text("DELETE FROM reports"))
        await s.execute(text("DELETE FROM access_tokens"))
        await s.execute(text("DELETE FROM users"))
        await s.execute(text("DELETE FROM interests"))
        await s.commit()

        # Create interests
        for name in INTEREST_NAMES:
            await s.execute(
                text("INSERT INTO interests (name) VALUES (:name)"),
                {"name": name},
            )
        await s.commit()

        # Get interest IDs
        result = await s.execute(text("SELECT id, name FROM interests"))
        interest_map = {row.name: row.id for row in result}

        # Create users
        user_ids = []
        for i in range(n_users):
            is_male = i % 2 == 0
            first = random.choice(FIRST_NAMES_M if is_male else FIRST_NAMES_F)
            last = random.choice(LAST_NAMES)
            gender = "MALE" if is_male else "FEMALE"
            age = random.randint(18, 35)
            location = random.choice(LOCATIONS)
            bio = random.choice(BIOS)
            email = f"{first.lower()}{i}@test.com"

            result = await s.execute(
                text("""
                    INSERT INTO users
                        (email, hashed_password, first_name, last_name,
                         gender, age, location, bio, is_active, is_superuser,
                         is_verified, rating)
                    VALUES
                        (:email, :pw, :fn, :ln, :gender, :age, :loc, :bio,
                         true, false, false, :rating)
                    RETURNING id
                """),
                {
                    "email": email,
                    "pw": PASSWORD_HASH,
                    "fn": first,
                    "ln": last,
                    "gender": gender,
                    "age": age,
                    "loc": location,
                    "bio": bio,
                    "rating": random.randint(0, 20),
                },
            )
            uid = result.scalar()
            user_ids.append(uid)

            # Assign 2-5 random interests
            chosen = random.sample(INTEREST_NAMES, random.randint(2, 5))
            for interest_name in chosen:
                await s.execute(
                    text("INSERT INTO user_interests (user_id, interest_id) VALUES (:uid, :iid)"),
                    {"uid": uid, "iid": interest_map[interest_name]},
                )

        await s.commit()

        # Create access tokens for all users
        for uid in user_ids:
            await s.execute(
                text("INSERT INTO access_tokens (token, user_id, created_at) VALUES (:token, :uid, NOW())"),
                {"token": f"test-token-{uid}", "uid": uid},
            )
        await s.commit()

        # Create some mutual matches
        matched_pairs = set()
        for _ in range(n_matches):
            a, b = random.sample(user_ids, 2)
            pair = (min(a, b), max(a, b))
            if pair in matched_pairs:
                continue
            matched_pairs.add(pair)

            await s.execute(
                text("INSERT INTO matchs (user_id, matched_user_id, is_mutual) VALUES (:a, :b, true)"),
                {"a": a, "b": b},
            )
            await s.execute(
                text("INSERT INTO matchs (user_id, matched_user_id, is_mutual) VALUES (:a, :b, true)"),
                {"a": b, "b": a},
            )
        await s.commit()

        print(f"Created {n_users} users, {len(INTEREST_NAMES)} interests, {len(matched_pairs)} mutual matches")
        print(f"Tokens: test-token-{{user_id}} (e.g. test-token-{user_ids[0]})")
        print(f"\nFirst users:")
        result = await s.execute(
            text("SELECT id, email, first_name, gender, age, location FROM users ORDER BY id LIMIT 5")
        )
        for row in result:
            print(f"  id={row.id} {row.email} ({row.first_name}, {row.gender}, {row.age}, {row.location})")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
