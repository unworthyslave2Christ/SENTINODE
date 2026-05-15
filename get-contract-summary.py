#BY GOD'S GRACE ALONE
#BY GOD'S GRACE ALONE
import json
import sys
import collections
from slither import Slither

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

target_contract_name = "Vault"
summary_payload = {}

# 1. Locate the contract workspace node safely
contract = next((c for c in slither.contracts if c.name == target_contract_name), None)

if contract:
    # 2. Extract structural deployment states verbatim from the source properties
    is_upgradeable_proxy = contract.is_upgradeable_proxy
    is_upgradeable = contract.is_upgradeable
    is_most_derived = contract in slither.contracts_derived

    summary_payload = {
        "contract": contract.name,
        "is_upgradeable_proxy": is_upgradeable_proxy,
        "is_upgradeable": is_upgradeable,
        "is_most_derived": is_most_derived,
        "inheritance_declarations": []
    }

    # 3. Mirror function filtering rules exactly as written in the printer code
    public_function = [
        (f.contract_declarer.name, f) for f in contract.functions 
        if (not f.is_shadowed and not f.is_constructor_variables)
    ]

    # Group functions by their exact contract_declarer (inheritance source)
    collect = collections.defaultdict(list)
    for dec_name, func_obj in public_function:
        collect[dec_name].append(func_obj)

    # 4. Process each declaration context to match visual color rules natively
    for origin_contract_name, functions in collect.items():
        # Alphabetically sort functions by full_name exactly like Slither's table engine
        sorted_functions = sorted(functions, key=lambda f: f.full_name)
        
        function_list = []
        for function in sorted_functions:
            # Replicate the visibility categorization hierarchy matching color schemas
            if function.visibility in ["external", "public"]:
                ui_color_group = "green"
            elif function.visibility in ["internal", "private"]:
                ui_color_group = "magenta"
            else:
                ui_color_group = "default"

            function_list.append({
                "full_name": function.full_name,
                "visibility": str(function.visibility),
                "ui_color_group": ui_color_group
            })

        summary_payload["inheritance_declarations"].append({
            "declared_in": origin_contract_name,
            "functions": function_list
        })

# Output the pure, unfragmented JSON structure straight to console stdout
print(json.dumps(summary_payload, indent=2))
