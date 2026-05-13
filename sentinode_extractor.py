import json
import sys
from slither import Slither

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

# Target 'Vault' or 'RebaseToken' dynamically
target_name = "RebaseToken"
contracts_found = slither.get_contract_from_name(target_name)

if not contracts_found:
    print(json.dumps({"error": f"Contract {target_name} not found."}))
    sys.exit(1)

contract = contracts_found[0]

# Extract cyclomatic complexity safely via Slither's metric helpers
def get_complexity(func):
    try:
        # Slither calculates cyclomatic complexity by counting conditional nodes
        return len([n for n in func.nodes if n.type.name in ["IF", "WHILE", "FOR", "DO_WHILE"]]) + 1
    except:
        return 1

# Build the payload mapping the visual columns from the screenshot
contract_payload = {
    "contract": contract.name,
    "contract_vars": [v.name for v in contract.state_variables if hasattr(v, 'name')],
    "inheritance": [c.name for c in contract.inheritance if hasattr(c, 'name')],
    "functions": []
}

for func in contract.functions:
    if func.is_shadowed:
        continue

    # Capture the exact high-level expression representations for external/internal flows
    internal_calls = []
    if hasattr(func, 'internal_calls'):
        # Matches internal state jumps or local custom error reverts
        internal_calls = [str(node.expression) for node in func.nodes if node.expression and "revert" in str(node.expression)]
        
    external_calls = []
    if hasattr(func, 'high_level_calls'):
        # Formats external interface queries e.g., i_rebaseToken.mint()
        for call in func.high_level_calls:
            try:
                external_calls.append(f"{call[0].name}.{call[1].name}")
            except:
                pass

    # Build the full-column schema
    func_data = {
        "name": func.full_name if hasattr(func, 'full_name') else func.name,
        "visibility": str(func.visibility),
        "modifiers": [m.name for m in func.modifiers if hasattr(m, 'name')],
        "reads": [v.name for v in func.state_variables_read if hasattr(v, 'name')],
        "writes": [v.name for v in func.state_variables_written if hasattr(v, 'name')],
        "internal_calls": internal_calls,
        "external_calls": [str(c) for c in func.high_level_calls] if hasattr(func, 'high_level_calls') else [],
        "cyclomatic_complexity": get_complexity(func)
    }
    contract_payload["functions"].append(func_data)

# Print clean JSON for the Node.js frontend layer parser
print(json.dumps(contract_payload, indent=2))
