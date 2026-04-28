"""Monkey-patch for Together.AI client to ensure proper role alternation."""

import copy
from typing import Any


def normalize_together_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Normalize messages to ensure strict user/assistant alternation required by Together.AI.
    
    Rules:
    1. System messages are kept at the start
    2. After system messages, roles must alternate: user -> assistant -> user -> assistant
    3. Consecutive messages with the same role are merged
    4. Tool messages are converted to user messages
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not messages:
        return []
    
    # Debug: log input messages
    logger.debug(f"Normalizing {len(messages)} messages for Together.AI")
    for i, msg in enumerate(messages[:5]):  # Log first 5
        logger.debug(f"  Input[{i}]: role={msg.get('role')}, content_len={len(str(msg.get('content', '')))}")
    
    # Step 1: Separate system messages and normalize others
    # Together.AI only allows ONE system message, so merge all system messages
    system_content_parts = []
    chat_msgs = []
    
    for msg in messages:
        msg_copy = copy.deepcopy(msg)
        role = msg_copy.get("role", "").lower()
        
        if role == "system":
            # Collect system message content (we'll merge into one)
            content = msg_copy.get("content", "")
            if content:
                system_content_parts.append(str(content))
        else:
            # Convert tool to user
            if role == "tool":
                msg_copy["role"] = "user"
            elif role not in ("user", "assistant"):
                # Skip invalid roles
                logger.debug(f"  Skipping message with invalid role: {role}")
                continue
            chat_msgs.append(msg_copy)
    
    # Create single merged system message if we have any
    system_msgs = []
    if system_content_parts:
        system_msgs = [{
            "role": "system",
            "content": "\n\n".join(system_content_parts)
        }]
    
    if not chat_msgs:
        logger.debug("No chat messages after filtering, returning system messages only")
        return system_msgs
    
    # Step 2: Merge consecutive messages with same role
    merged = []
    for msg in chat_msgs:
        role = msg.get("role", "").lower()
        content = msg.get("content", "")
        
        # Convert content to string
        if not isinstance(content, str):
            content = str(content) if content else ""
        
        # If same role as last, merge content
        if merged and merged[-1].get("role", "").lower() == role:
            prev_content = merged[-1].get("content", "")
            if isinstance(prev_content, str):
                merged[-1]["content"] = f"{prev_content}\n\n{content}".strip() if content else prev_content
            else:
                merged[-1]["content"] = content
        else:
            merged.append(msg)
    
    logger.debug(f"After merging: {len(merged)} messages")
    for i, msg in enumerate(merged[:5]):
        logger.debug(f"  Merged[{i}]: role={msg.get('role')}")
    
    # Step 3: Ensure strict alternation
    result = system_msgs.copy()
    expected_role = "user"  # After system, must start with user
    
    for msg in merged:
        role = msg.get("role", "").lower()
        
        # If role doesn't match expected, fix it
        if role != expected_role:
            logger.debug(f"  Role mismatch: expected {expected_role}, got {role}. Fixing alternation.")
            if expected_role == "user":
                # Need user but got assistant - insert empty user first
                result.append({"role": "user", "content": ""})
            else:
                # Need assistant but got user - this means we have user->user, merge with previous
                if result and result[-1].get("role", "").lower() == "user":
                    # Merge this user message with the previous one
                    prev_content = result[-1].get("content", "")
                    new_content = msg.get("content", "")
                    if isinstance(prev_content, str) and isinstance(new_content, str):
                        result[-1]["content"] = f"{prev_content}\n\n{new_content}".strip() if new_content else prev_content
                    else:
                        result[-1]["content"] = new_content
                    # Don't append msg, we merged it
                    expected_role = "assistant"  # Next should be assistant
                    continue
        
        result.append(msg)
        
        # Toggle expected role
        expected_role = "assistant" if expected_role == "user" else "user"
    
    # Final validation: ensure alternation
    final_result = []
    prev_role = None
    for msg in result:
        role = msg.get("role", "").lower()
        if role == "system":
            final_result.append(msg)
            prev_role = None  # Reset after system
        elif role in ("user", "assistant"):
            if prev_role == role:
                # Still have consecutive same roles - merge
                prev_content = final_result[-1].get("content", "")
                new_content = msg.get("content", "")
                if isinstance(prev_content, str) and isinstance(new_content, str):
                    final_result[-1]["content"] = f"{prev_content}\n\n{new_content}".strip() if new_content else prev_content
                else:
                    final_result[-1]["content"] = new_content
            else:
                final_result.append(msg)
                prev_role = role
    
    logger.debug(f"Final normalized: {len(final_result)} messages")
    for i, msg in enumerate(final_result[:5]):
        logger.debug(f"  Final[{i}]: role={msg.get('role')}")
    
    # Verify alternation (log warning if violation detected)
    system_count = len(system_msgs)  # Should be 0 or 1
    if len(final_result) > system_count:
        chat_roles = [msg.get('role') for msg in final_result[system_count:]]
        for i in range(len(chat_roles) - 1):
            if chat_roles[i] == chat_roles[i+1]:
                logger.warning(f"Consecutive same roles at index {i}: {chat_roles[i]}")
    
    return final_result


def patch_together_client():
    """Monkey-patch AG2's Together client to use our normalized message function."""
    try:
        import autogen.oai.together as together_module
        
        # Store original for reference
        original_func = together_module.oai_messages_to_together_messages
        
        # Replace the function
        together_module.oai_messages_to_together_messages = normalize_together_messages
        
        # Verify patch was applied
        if together_module.oai_messages_to_together_messages is normalize_together_messages:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Successfully patched Together.AI message normalization")
            return True
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to verify Together.AI patch")
            return False
    except (ImportError, AttributeError) as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Together.AI patch not available: {e}")
        return False

