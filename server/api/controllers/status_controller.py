"""Status controller."""
import os
import logging
from fastapi import HTTPException
from typing import Dict

logger = logging.getLogger(__name__)


class StatusController:
    """Controller for status endpoints."""
    
    def get_status(self) -> Dict:
        """
        Get server status including API key availability.
        
        Returns:
            Status response dictionary
        """
        try:
            cerebras_api_key = os.environ.get("CEREBRAS_API_KEY")
            llm_configured = bool(cerebras_api_key)
            
            # Check if LLM parser is actually available
            llm_parser_available = False
            if llm_configured:
                try:
                    from cerebras.cloud.sdk import Cerebras
                    llm_parser_available = True
                except ImportError:
                    llm_parser_available = False
                except Exception:
                    llm_parser_available = False
            
            return {
                "ok": True,
                "cerebras_api_key_configured": llm_configured,
                "llm_parser_available": llm_parser_available,
                "server_ready": True,
                "supports_auto_refresh": True  # Server supports polling for changes
            }
        except Exception as e:
            error_msg = f"Failed to get status: {str(e)}"
            logger.error(f"ERROR in StatusController.get_status: {error_msg}", exc_info=True)
            return {
                "ok": False,
                "error": error_msg,
                "cerebras_api_key_configured": False,
                "llm_parser_available": False,
                "server_ready": False,
                "supports_auto_refresh": False
            }


