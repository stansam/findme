from enum import Enum

class UserRole(Enum):
    REGULAR = "regular"
    VERIFIED = "verified"
    ADMIN = "admin"


class MissingPersonStatus(Enum):
    MISSING = "missing"
    FOUND = "found"
    INVESTIGATING = "investigating"
    CLOSED = "closed"


class ReportStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"