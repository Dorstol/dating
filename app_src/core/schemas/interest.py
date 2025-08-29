from pydantic import BaseModel, Field, field_validator


class InterestBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Interest name")


class InterestCreate(InterestBase):
    pass


class InterestRead(InterestBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True


class UserInterestsUpdate(BaseModel):
    interests: list[str] = Field(..., description="List of interest names")

    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Interests list cannot be empty")
        if len(v) > 10:
            raise ValueError("Interests list cannot be longer than 10 items")

        cleaned_interests = []
        for interest in v:
            cleaned = interest.strip().lower()
            if cleaned and len(cleaned) <= 50:
                cleaned_interests.append(cleaned)

        if not cleaned_interests:
            raise ValueError("Interests list cannot be empty")

        return cleaned_interests


class UserInterestsResponse(BaseModel):
    interests: list[InterestRead]
    count: int

    class Config:
        from_attributes = True
