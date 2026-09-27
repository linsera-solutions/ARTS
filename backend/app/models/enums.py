from enum import Enum


class UserRole(str, Enum):
    ADMINISTRATOR = "Administrator"
    REVIEWER = "Reviewer"
    COORDINATOR = "Coordinator"


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"


class ApplicantStatus(str, Enum):
    ACTIVE = "Active"
    WITHDRAWN = "Withdrawn"
    ARCHIVED = "Archived"


class ApplicationStatus(str, Enum):
    RECEIVED = "Received"
    UNDER_REVIEW = "Under Review"
    SHORTLISTED = "Shortlisted"
    DISCUSSION_INTERVIEW = "Discussion / Interview"
    SELECTED = "Selected"
    NOT_SELECTED = "Not Selected"
    WITHDRAWN = "Withdrawn"


class RoleStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    FILLED = "Filled"


class TeamStatus(str, Enum):
    FORMING = "Forming"
    ACTIVE = "Active"
    CLOSED = "Closed"


class MembershipStatus(str, Enum):
    ACTIVE = "Active"
    REMOVED = "Removed"
    COMPLETED = "Completed"


class ProficiencyLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"


class EvaluationRecommendation(str, Enum):
    ADVANCE = "Advance"
    REJECT = "Reject"
    WAITLIST = "Waitlist"
    NEEDS_DISCUSSION = "Needs Discussion"


class EvaluationStatus(str, Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"


class NoteRelatedEntityType(str, Enum):
    APPLICANT = "Applicant"
    APPLICATION = "Application"


class NoteVisibility(str, Enum):
    INTERNAL = "Internal"
    PRIVATE = "Private"
    PUBLIC = "Public"


class InterviewStatus(str, Enum):
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
