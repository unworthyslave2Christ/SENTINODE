import json
import sys
from slither import Slither
from slither.core.declarations.function import Function

# 1. Mirror get_msg_sender_checks verbatim from the provided printer class source
def get_msg_sender_checks(function: Function) -> list[str]:
    all_functions = [
        ir.function for ir in function.all_internal_calls() if isinstance(ir.function, Function)
    ] + [function]
    
    all_nodes_ = [f.nodes for f in all_functions]
    all_nodes = [item for sublist in all_nodes_ for item in sublist]
    
    all_conditional_nodes = [
        n for n in all_nodes if n.contains_if() or n.contains_require_or_assert()
    ]
    
    all_conditional_nodes_on_msg_sender = [
        str(n.expression) for n in all_conditional_nodes if "msg.sender" in [v.name for v in n.solidity_variables_read]
    ]
    return all_conditional_nodes_on_msg_sender

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

target_contract_name = "Vault"
auth_payload = {}

# 2. Extract target contract object safely from standard iteration context
contract = next((c for c in slither.contracts if c.name == target_contract_name), None)

if contract:
    auth_payload = {
        "contract": contract.name,
        "functions": []
    }
    
    # 3. Process every single function and track the exact data mappings verbatim
    for function in contract.functions:
        state_variables_written = [
            v.name for v in function.all_state_variables_written() if v.name
        ]
        
        # Pull authentications using the exact code routine from Trail of Bits
        msg_sender_condition = get_msg_sender_checks(function)
        
        auth_payload["functions"].append({
            "name": function.name,
            "state_variables_written": sorted(state_variables_written),
            "conditions_on_msg_sender": sorted(msg_sender_condition)
        })

# Output the pure, unfragmented JSON structure straight to console stdout
print(json.dumps(auth_payload, indent=2))
