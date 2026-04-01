from enum import Enum


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class ReportReasonEnum(str, Enum):
    SPAM = "Spam"
    FAKE = "Fake"
    HARASSMENT = "Harassment"
    INAPPROPRIATE_CONTENT = "Inappropriate Content"
