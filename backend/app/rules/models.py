from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Category(str, Enum):
    SQLI = "SQLI"
    XSS = "XSS"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    COMMAND_INJECTION = "COMMAND_INJECTION"


class Rule(BaseModel):
    id: str
    version: int
    name: str
    severity: Severity
    priority: int  # lower = higher priority
    pattern: str
    category: Category
    description: str = ""


class RuleSet(BaseModel):
    version: str
    released_at: str
    rules: list[Rule]
