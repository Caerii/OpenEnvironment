"""Service layer for running multi-agent terrain design loops."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np

from ..semantic.multi_agent.workflow import run_multi_agent_terrain_design

logger = logging.getLogger(__name__)


class MultiAgentService:
    """Coordinates the AG2 workflow and applies resulting actions."""

    def __init__(self, terrain_service, state_service):
        self.terrain_service = terrain_service
        self.state_service = state_service

    def run_design(
        self,
        command_text: str,
        profile: Optional[str] = None,
        max_rounds: int = 6,
    ) -> Dict[str, Optional[object]]:
        """Run the multi-agent workflow and apply resulting actions."""

        scene_state = self.state_service.get_state()
        workflow_result = run_multi_agent_terrain_design(
            command=command_text,
            scene_state=scene_state,
            profile=profile,
            max_rounds=max_rounds,
        )

        actions = workflow_result.get("actions") or []

        heightmap: Optional[np.ndarray] = None
        updated_state: Optional[Dict] = None
        splatmap: Optional[np.ndarray] = None

        if actions:
            try:
                heightmap, updated_state, splatmap = self.terrain_service.generate_terrain(
                    command_text=command_text,
                    actions=actions,
                )
            except Exception as exc:
                logger.error("Failed to apply multi-agent actions: %s", exc, exc_info=True)
                # Do not abort workflow metadata; caller can inspect error state.

        return {
            "workflow": workflow_result,
            "heightmap": heightmap,
            "state": updated_state,
            "splatmap": splatmap,
            "actions": actions,
        }


