import json
import sys
from slither import Slither
from slither.core.declarations import SolidityFunction
from slither.slithir.operations import SolidityCall

# 1. Mirror the native target list definition verbatim from the source file
require_or_assert = [
    SolidityFunction("assert(bool)"),
    SolidityFunction("require(bool)"),
    SolidityFunction("require(bool,string)"),
    SolidityFunction("require(bool,error)"),
]

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

target_contract_name = "SlitherTest"
require_payload = {}

# 2. Safely locate the target contract object within the derived contracts collection
contract = next((c for c in slither.contracts_derived if c.name == target_contract_name), None)

if contract:
    require_payload = {
        "contract": contract.name,
        "functions": []
    }
    
    # 3. Process every function and extract SlithIR operations verbatim
    for function in contract.functions:
        # Pull low-level IR execution blocks
        slithir_ops = function.all_slithir_operations()
        
        # Filter for matching require/assert Solidity calls strictly by type
        matched_ops = [
            ir for ir in slithir_ops 
            if isinstance(ir, SolidityCall) and ir.function in require_or_assert
        ]
        
        # Map the unique execution nodes to their raw text expressions
        unique_nodes = set([ir.node for ir in matched_ops])
        expressions = [str(m.expression) for m in unique_nodes if m.expression]
        
        require_payload["functions"].append({
            "name": function.name,
            "require_or_assert_expressions": sorted(expressions)
        })

# Output the pure, unfragmented JSON structure straight to console stdout
print(json.dumps(require_payload, indent=2))
