import json
import sys
from slither import Slither

#  Variable Order Direct Reimplementation

try:
    # Initialize Slither on the local Foundry directory
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

# Extract the RebaseToken contract object safely from the derived manifest array
contract = next((c for c in slither.contracts_derived if c.name == "RebaseToken"), None)

if not contract:
    print(json.dumps({"error": "Contract 'RebaseToken' not found in derived contracts."}))
    sys.exit(1)

# Replicate the data mapping logic from VariableOrder.output() directly to JSON
storage_data = {
    "contract": contract.name,
    "variables": []
}

# 1. Process standard storage state variables
for variable in contract.storage_variables_ordered:
    slot, offset = contract.compilation_unit.storage_layout_of(contract, variable)
    storage_data["variables"].append({
        "name": variable.canonical_name,
        "type": str(variable.type),
        "slot": slot,
        "offset": offset,
        "state_type": "Storage"
    })

# 2. Process transient state variables (Solidity 0.8.24+)
if hasattr(contract, 'transient_variables_ordered'):
    for variable in contract.transient_variables_ordered:
        slot, offset = contract.compilation_unit.storage_layout_of(contract, variable)
        storage_data["variables"].append({
            "name": variable.canonical_name,
            "type": str(variable.type),
            "slot": slot,
            "offset": offset,
            "state_type": "Transient"
        })

# Output the raw structural data payload without table decorators
print(json.dumps(storage_data, indent=2))
