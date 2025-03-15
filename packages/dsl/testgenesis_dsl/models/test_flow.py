"""TestGenesis DSL models for defining test flows."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Action:
    """Represents a user action in a test flow."""

    type: str
    target: str
    data: Optional[Dict[str, Any]] = None
    assertions: Optional[List[str]] = None


@dataclass
class TestFlow:
    """Represents a sequence of user actions that form a test flow."""

    name: str
    actions: List[Action]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    frequency: int = 1

    def get_pattern(self) -> str:
        """Get a string representation of the action pattern for comparison."""
        return "|".join(f"{a.type}:{a.target}" for a in self.actions)

    def save(self, path: Path) -> None:
        """Save the test flow to a JSON file."""
        import json

        data = {
            "name": self.name,
            "frequency": self.frequency,
            "actions": [
                {
                    "type": action.type,
                    "target": action.target,
                    **({"data": action.data} if action.data is not None else {}),
                    **({"assertions": action.assertions} if action.assertions is not None else {}),
                }
                for action in self.actions
            ],
        }

        path.write_text(json.dumps(data, indent=2))


@dataclass
class UserJourney:
    """Represents a collection of related test flows."""

    name: str
    flows: List[TestFlow]
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
