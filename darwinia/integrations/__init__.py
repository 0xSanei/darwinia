"""
Darwinia Integrations — composability interfaces for cross-skill interop.

Provides:
- SkillBridge: programmatic API for other skills to call Darwinia
- SkillRegistry: discover and call external skills from within Darwinia
"""

from .skill_bridge import SkillBridge, SkillRegistry

__all__ = ["SkillBridge", "SkillRegistry"]
