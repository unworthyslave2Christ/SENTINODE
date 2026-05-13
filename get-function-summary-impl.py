import json
import sys
from slither import Slither

try:
    # Initialize Slither targeting your Foundry workspace folder
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

# Safely locate the target contract object matching RebaseToken
contract = next((c for c in slither.contracts if c.name == "RebaseToken"), None)

if not contract:
    print(json.dumps({"error": "Contract 'RebaseToken' not found."}))
    sys.exit(1)

# Extract raw tuple properties from the native get_summary() helper
(name, inheritance, var, func_summaries, modif_summaries) = contract.get_summary()

# Map the raw data structures directly into an un-formatted JSON block
verbatim_data = {
    "contract": name,
    "contract_vars": var,
    "inheritance": inheritance,
    "functions": [],
    "modifiers": []
}

# Process each function summary tuple row verbatim
for (
    _c_name, f_name, visi, modifiers, read, write, internal_calls, external_calls, cyclomatic_complexity
) in func_summaries:
    verbatim_data["functions"].append({
        "name": f_name,
        "visibility": visi,
        "modifiers": sorted(modifiers),
        "read": sorted(read),
        "write": sorted(write),
        "internal_calls": sorted(internal_calls),
        "external_calls": sorted(external_calls),
        "cyclomatic_complexity": cyclomatic_complexity
    })

# Process each modifier summary tuple row verbatim
for (
    _c_name, m_name, visi, _, read, write, internal_calls, external_calls, cyclomatic_complexity
) in modif_summaries:
    verbatim_data["modifiers"].append({
        "name": m_name,
        "visibility": visi,
        "read": sorted(read),
        "write": sorted(write),
        "internal_calls": sorted(internal_calls),
        "external_calls": sorted(external_calls),
        "cyclomatic_complexity": cyclomatic_complexity
    })

# Output the pure, unfragmented JSON structure straight to stdout
print(json.dumps(verbatim_data, indent=2))
