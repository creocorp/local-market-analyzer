from __future__ import annotations

from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass

import yaml


# All YAML configuration (including prompt templates) lives in backend/config/
PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "config"


@dataclass(frozen=True)
class PromptTemplate:
    system: str
    user: str

    def render(self, **kwargs: object) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) with variables substituted."""
        return (
            self.system.strip().format(**kwargs),
            self.user.strip().format(**kwargs),
        )


@lru_cache(maxsize=32)
def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_prompt(name: str, file: str = "prompts") -> PromptTemplate:
    """Load a named prompt template from a YAML file in the prompts directory.

    Args:
        name: The prompt key inside the YAML (e.g. "trading_analysis").
        file: The YAML filename without extension (default: "default").
    """
    path = PROMPTS_DIR / f"{file}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    data = _load_yaml(path)
    prompts = data.get("prompts", {})
    entry = prompts.get(name)

    if entry is None:
        available = ", ".join(prompts.keys())
        raise KeyError(f"Prompt '{name}' not found in {file}.yaml. Available: {available}")

    return PromptTemplate(
        system=entry.get("system", ""),
        user=entry.get("user", ""),
    )
