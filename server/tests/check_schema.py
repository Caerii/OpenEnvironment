#!/usr/bin/env python
"""Check generated tool schemas."""

from semantic.tools.executor import ToolExecutor
from semantic.tools.schema import get_all_tool_schemas
import json

executor = ToolExecutor()
schemas = get_all_tool_schemas(executor.get_tool_functions())

print(f"Generated {len(schemas)} tool schemas\n")

for schema in schemas:
    name = schema["function"]["name"]
    params = schema["function"]["parameters"]["properties"]
    
    print(f"=== {name} ===")
    
    # Check for arrays and objects
    for param_name, param_info in params.items():
        if param_info["type"] == "array":
            if "items" not in param_info:
                print(f"  ERROR {param_name}: array missing 'items'")
            else:
                print(f"  OK {param_name}: array with items={param_info['items']}")
        elif param_info["type"] == "object":
            if "properties" not in param_info:
                print(f"  ERROR {param_name}: object missing 'properties'")
            else:
                print(f"  OK {param_name}: object with properties")
    print()

# Show one full schema
print("\n=== SAMPLE SCHEMA (get_feature_details) ===")
sample = next(s for s in schemas if s["function"]["name"] == "get_feature_details")
print(json.dumps(sample, indent=2))

