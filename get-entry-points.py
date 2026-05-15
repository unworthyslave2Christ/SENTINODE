import json
import sys
from pathlib import Path
from slither import Slither
from slither.core.declarations.function_contract import FunctionContract

# 1. Replicate Slither's native check for test file paths
def is_test_file(file_path):
    path_str = str(file_path).lower()
    return "test" in path_str or "t.sol" in path_str

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

# Keep output focused on your core workspace file metrics
target_contract_name = "RebaseToken"
entry_point_data = {}

# 2. Mirror the contract filtering logic loop verbatim
filtered_contracts = []
for c in slither.contracts_derived:
    filename = c.source_mapping.filename.absolute if c.source_mapping.filename else ""
    
    if (
        not c.is_test and 
        not c.is_from_dependency() and 
        not is_test_file(Path(filename)) and 
        not c.is_interface and 
        not c.is_library and 
        not c.is_abstract
    ):
        filtered_contracts.append(c)

# Sort contracts by name alphabetically matching Slither's table engine sequence
filtered_contracts.sort(key=lambda x: x.name)

# 3. Process the target contract matching RebaseToken
contract = next((c for c in filtered_contracts if c.name == target_contract_name), None)

if contract:
    # Mirror entry points filtering algorithm verbatim
    entry_points = [
        f for f in contract.functions if (
            f.visibility in ["public", "external"] and 
            isinstance(f, FunctionContract) and 
            not f.view and 
            not f.pure and 
            not f.is_shadowed
        )
    ]

    # Mirror _get_inheritance_chain verbatim
    inheritance_chain = []
    for base in contract.inheritance:
        if not base.is_interface and not base.is_library:
            inheritance_chain.append(base.name)

    # Mirror _get_variables_info verbatim
    variables_info = []
    for variable in contract.storage_variables_ordered:
        var_type = str(variable.type)
        inherited_from = variable.contract.name if variable.contract != contract else "Local"
        variables_info.append({
            "variable_name": variable.name,
            "type": var_type,
            "inherited_from": inherited_from
        })

    # Mirror _add_function_rows logic loops verbatim
    functions_info = []
    sorted_entry_points = sorted(
        entry_points,
        key=lambda x: (
            x.contract_declarer != contract,
            x.contract_declarer.name if x.contract_declarer != contract else "",
            x.source_mapping.start if x.source_mapping else 0,
        ),
    )

    for f in sorted_entry_points:
        inherited = f.contract_declarer.name if f.contract_declarer != contract else "Local"
        modifiers = [m.name for m in f.modifiers]
        if f.payable:
            modifiers.append("payable")

        functions_info.append({
            "full_name": f.full_name,
            "modifiers": modifiers,
            "inherited_from": inherited,
            "is_special": f.is_constructor or f.name in ["receive", "fallback"]
        })

    entry_point_data = {
        "contract": contract.name,
        "source_mapping": str(contract.source_mapping),
        "inheritance_chain": inheritance_chain,
        "variables_info": variables_info,
        "entry_point_functions": functions_info
    }

# Output unfragmented, official database parameters straight to console stdout
print(json.dumps(entry_point_data, indent=2))
