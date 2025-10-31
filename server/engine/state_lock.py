"""Atomic state file operations with cross-platform locking."""
import os
import json
import sys
import tempfile
from typing import Dict, Optional
from pathlib import Path

# Cross-platform file locking
if sys.platform == 'win32':
    import msvcrt
    def lock_file(file_obj):
        """Lock file on Windows."""
        try:
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, 1)
        except IOError:
            pass  # Lock may already be held
    
    def unlock_file(file_obj):
        """Unlock file on Windows."""
        try:
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
        except IOError:
            pass
else:
    import fcntl
    def lock_file(file_obj):
        """Lock file on Unix."""
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
    
    def unlock_file(file_obj):
        """Unlock file on Unix."""
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)


def atomic_read_state(state_path: str, default: Optional[Dict] = None) -> Dict:
    """
    Atomically read state file with locking.
    
    Args:
        state_path: Path to state JSON file
        default: Default state if file doesn't exist
        
    Returns:
        State dictionary
    """
    if default is None:
        default = {"features": [], "seed": 0}
    
    if not os.path.exists(state_path):
        return default.copy()
    
    try:
        with open(state_path, "r") as f:
            lock_file(f)
            try:
                state = json.load(f)
                # Validate state structure
                if not isinstance(state, dict):
                    raise ValueError("State is not a dictionary")
                if "features" not in state:
                    state["features"] = []
                if "seed" not in state:
                    state["seed"] = 0
                return state
            finally:
                unlock_file(f)
    except (json.JSONDecodeError, ValueError, IOError) as e:
        # Corrupted state - return default
        print(f"Warning: Failed to read state file ({e}), using default")
        return default.copy()


def atomic_write_state(state: Dict, state_path: str, backup: bool = True):
    """
    Atomically write state file with locking and backup.
    
    Args:
        state: State dictionary to write
        state_path: Path to state JSON file
        backup: Whether to create a backup before writing
    """
    # Validate state
    if not isinstance(state, dict):
        raise ValueError("State must be a dictionary")
    if "features" not in state:
        state["features"] = []
    if "seed" not in state:
        state["seed"] = 0
    
    # Create backup if requested
    if backup and os.path.exists(state_path):
        backup_path = state_path + ".backup"
        try:
            with open(state_path, "r") as src, open(backup_path, "w") as dst:
                lock_file(src)
                try:
                    dst.write(src.read())
                finally:
                    unlock_file(src)
        except IOError:
            pass  # Backup failed, continue anyway
    
    # Atomic write: write to temp file, then rename
    temp_path = state_path + ".tmp"
    try:
        with open(temp_path, "w") as f:
            lock_file(f)
            try:
                json.dump(state, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            finally:
                unlock_file(f)
        
        # Atomic rename (cross-platform)
        if sys.platform == 'win32':
            # Windows: remove target first if exists
            if os.path.exists(state_path):
                os.remove(state_path)
            os.rename(temp_path, state_path)
        else:
            # Unix: rename is atomic
            os.replace(temp_path, state_path)
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise IOError(f"Failed to write state file: {e}") from e

