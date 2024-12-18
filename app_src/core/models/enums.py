from enum import Enum


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class InterestEnum(str, Enum):
    SPORTS = "Sports"
    MUSIC = "Music"
    ART = "Art"
    OTHER = "Other"