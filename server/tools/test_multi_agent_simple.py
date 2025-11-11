"""Simple test script to verify multi-agent workflow is working."""

import os
import sys
from pathlib import Path

# Add server to path
server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))

from dotenv import load_dotenv

load_dotenv()

# Import after path setup
from server.bootstrap import ensure_bootstrapped
ensure_bootstrapped()

from server.semantic.multi_agent.workflow import run_multi_agent_terrain_design

if __name__ == "__main__":
    print("Testing multi-agent workflow...")
    print(f"TOGETHER_API_KEY: {'SET' if os.environ.get('TOGETHER_API_KEY') else 'NOT SET'}")
    print(f"LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', 'together')}")
    
    try:
        result = run_multi_agent_terrain_design(
            command="create a simple mountain",
            max_rounds=2,
        )
        print(f"Success! Got {len(result.get('actions', []))} actions")
        print(f"Summary: {result.get('summary', '')[:200]}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

