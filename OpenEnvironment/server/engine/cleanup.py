"""File cleanup utilities - Manage asset retention and cleanup."""
import os
import time
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Retention policy: Keep last N assets + any newer than X hours
MAX_ASSETS_TO_KEEP = 50  # Always keep last 50 generations
MIN_AGE_HOURS = 24  # Keep assets newer than 24 hours regardless of count


def cleanup_old_assets(assets_dir: str, keep_state: bool = True):
    """
    Clean up old terrain assets based on retention policy.
    
    Args:
        assets_dir: Directory containing terrain assets
        keep_state: Whether to keep terrain_state.json (default: True)
    """
    if not os.path.exists(assets_dir):
        return
    
    # Find all asset files
    asset_files: List[Tuple[str, float]] = []
    
    for filename in os.listdir(assets_dir):
        filepath = os.path.join(assets_dir, filename)
        
        # Skip directories and state files
        if os.path.isdir(filepath):
            continue
        if keep_state and filename == "terrain_state.json":
            continue
        if filename.endswith(".backup") or filename.endswith(".tmp"):
            continue
        
        # Get modification time
        try:
            mtime = os.path.getmtime(filepath)
            asset_files.append((filepath, mtime))
        except OSError:
            continue
    
    if len(asset_files) <= MAX_ASSETS_TO_KEEP:
        return  # No cleanup needed
    
    # Sort by modification time (newest first)
    asset_files.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate cutoff time
    cutoff_time = time.time() - (MIN_AGE_HOURS * 3600)
    
    # Delete old files
    deleted_count = 0
    for filepath, mtime in asset_files[MAX_ASSETS_TO_KEEP:]:
        # Keep if newer than cutoff
        if mtime > cutoff_time:
            continue
        
        try:
            os.remove(filepath)
            deleted_count += 1
        except OSError as e:
            logger.warning(f"Failed to delete {filepath}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old asset files")


def cleanup_temp_files(assets_dir: str):
    """Clean up temporary files (.tmp, .backup)."""
    if not os.path.exists(assets_dir):
        return
    
    deleted_count = 0
    for filename in os.listdir(assets_dir):
        if filename.endswith(".tmp") or filename.endswith(".backup"):
            filepath = os.path.join(assets_dir, filename)
            try:
                # Only delete if older than 1 hour
                mtime = os.path.getmtime(filepath)
                if time.time() - mtime > 3600:
                    os.remove(filepath)
                    deleted_count += 1
            except OSError:
                pass
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} temporary files")

