"""TestGenesis DSL models for defining test flows."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class UserAction:
    """Represents a single user action in a test flow."""
    
    type: str  # navigation, click, form, etc.
    target: str  # URL, selector, etc.
    assertions: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    wait_for: Optional[str] = None
    timeout: int = 5000


@dataclass
class TestFlow:
    """Represents a sequence of user actions that form a test."""
    
    name: str
    actions: List[UserAction]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def get_pattern(self) -> str:
        """Get a string representation of the action pattern for comparison."""
        return "|".join(f"{a.type}:{a.target}" for a in self.actions)


@dataclass
class UserJourney:
    """Represents a collection of related test flows."""
    
    name: str
    flows: List[TestFlow]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list) 