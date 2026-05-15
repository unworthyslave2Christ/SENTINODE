#BY GOD'S GRACE ALONE
import json
import sys
import re
import subprocess
from pathlib import Path
from collections import defaultdict
from typing import NamedTuple
from slither import Slither
from slither.core.declarations import SolidityFunction, Function, Contract, Enum
from slither.core.declarations.function_contract import FunctionContract
from slither.core.declarations.solidity_variables import SolidityVariableComposed
from slither.core.variables.state_variable import StateVariable
from slither.core.variables.variable import Variable
from slither.core.cfg.node import Node
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.operations import (
    Operation, SolidityCall, LowLevelCall, HighLevelCall, 
    EventCall, NewContract, Send, Transfer, InternalDynamicCall, 
    InternalCall, TypeConversion, Member
)
from slither.slithir.operations.binary import Binary
from slither.slithir.variables import Constant, ReferenceVariable
from slither.visitors.expression.constants_folding import ConstantFolding, NotConstant

# Define official SlithIR validation checkpoints for assertions
require_or_assert_targets = [
    SolidityFunction("assert(bool)"),
    SolidityFunction("require(bool)"),
    SolidityFunction("require(bool,string)"),
    SolidityFunction("require(bool,error)"),
]

def json_serializable(cls):
    my_super = super
    def as_dict(self):
        yield dict(zip(self._fields, my_super(cls, self).__iter__(), strict=False))
    cls.__iter__ = as_dict
    return cls

@json_serializable
class ConstantValue(NamedTuple):
    value: str
    type: str

def _get_name(f: Function | Variable) -> str:
    if isinstance(f, Function):
        if f.is_fallback or f.is_receive:
            return "()"
        return f.solidity_signature
    return str(f)

def _is_constant(f: Function) -> bool:
    if f.view or f.pure:
        if not f.compilation_unit.solc_version.startswith("0.4"):
            return True
    if f.payable or not f.is_implemented or f.contains_assembly:
        return False
    if f.all_state_variables_written():
        return False
    for ir in f.all_slithir_operations():
        if isinstance(ir, (InternalDynamicCall, EventCall, NewContract, LowLevelCall, Send, Transfer)):
            return False
        if isinstance(ir, SolidityCall) and ir.function in [SolidityFunction("selfdestruct(address)"), SolidityFunction("suicide(address)")]:
            return False
        if isinstance(ir, HighLevelCall):
            if not (isinstance(ir.function, Variable) or ir.function.view or ir.function.pure):
                return False
    return True

def _extract_constant_from_read(ir, r, all_cst_used, all_cst_used_in_binary, context_explored):
    var_read = r.points_to_origin if isinstance(r, ReferenceVariable) else r
    if isinstance(ir, Member) or not isinstance(var_read, Variable):
        return
    if var_read.is_constant:
        value_type = ir.type.type if hasattr(ir, 'type') and hasattr(ir.type, 'type') else (ir.type if hasattr(ir, 'type') else var_read.type)
        try:
            value = ConstantFolding(var_read.expression, value_type).result()
            all_cst_used.append(ConstantValue(str(value), str(value_type)))
        except NotConstant:
            pass
    if isinstance(var_read, StateVariable) and var_read.node_initialization:
        if var_read.node_initialization in context_explored:
            return
        context_explored.add(var_read.node_initialization)
        if var_read.node_initialization.irs:
            _extract_constants_from_irs(var_read.node_initialization.irs, all_cst_used, all_cst_used_in_binary, context_explored)

def _extract_constant_from_binary(ir: Binary, all_cst_used: list, all_cst_used_in_binary: dict):
    for r in ir.read:
        if isinstance(r, Constant):
            all_cst_used_in_binary[str(ir.type)].append(ConstantValue(str(r.value), str(r.type)))
    if isinstance(ir.variable_left, Constant) or isinstance(ir.variable_right, Constant):
        if ir.lvalue:
            try:
                type_ = ir.lvalue.type
                cst = ConstantFolding(ir.expression, type_).result()
                all_cst_used.append(ConstantValue(str(cst.value), str(type_)))
            except NotConstant:
                pass

def _extract_constants_from_irs(irs: list, all_cst_used: list, all_cst_used_in_binary: dict, context_explored: set) -> None:
    for ir in irs:
        if isinstance(ir, Binary):
            _extract_constant_from_binary(ir, all_cst_used, all_cst_used_in_binary)
        if isinstance(ir, TypeConversion) and isinstance(ir.variable, Constant):
            value_type = ir.type.type if hasattr(ir.type, 'type') else ir.type
            all_cst_used.append(ConstantValue(str(ir.variable.value), str(value_type)))
            continue
        if isinstance(ir, Member) and isinstance(ir.variable_left, Enum) and isinstance(ir.variable_right, Constant):
            try:
                internal_num = ir.variable_left.values.index(ir.variable_right.value)
                all_cst_used.append(ConstantValue(str(internal_num), "uint256"))
            except ValueError:
                pass
        for r in ir.read:
            if isinstance(r, Constant):
                all_cst_used.append(ConstantValue(str(r.value), str(r.type)))
            _extract_constant_from_read(ir, r, all_cst_used, all_cst_used_in_binary, context_explored)

# [CONTINUED IN PART 2]
#BY GOD'S GRACE ALONE
# Continuation of sentinode_complete_core.py

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

# --- 1. DYNAMIC JAVASCRIPT PRE-PROCESSOR ORCHESTRATION ---
print("--- RUNNING NODE.JS PROJECT TRACE ENGINE MATRIX ---")
try:
    with open("processAllCfgs.js", "r", encoding="utf-8") as js_file:
        js_code = js_file.read()
    
    if "fs.writeFileSync('./generated_cfgs/raw_trace_map.json'" not in js_code:
        patch_line = "\nfs.writeFileSync('./generated_cfgs/raw_trace_map.json', JSON.stringify(SENTINODE_MAP, null, 2));\n"
        with open("processAllCfgs.js", "a", encoding="utf-8") as js_file:
            js_file.write(patch_line)
            
    subprocess.run(["node", "processAllCfgs.js"], check=True, capture_output=True, text=True)
except Exception as e:
    print(f"Preprocessor Bridge Status Tracker Failure: {str(e)}")

# --- 2. LOAD VERBATIM JAVASCRIPT OUTPUT MAP & OMIT TARGET FIELDS ---
js_cfg_lookup_cache = {}
raw_trace_file = Path("./generated_cfgs/raw_trace_map.json")

if raw_trace_file.exists():
    try:
        with open(raw_trace_file, "r", encoding="utf-8") as f:
            raw_cache_data = json.load(f)
            
        print(f"Loaded {len(raw_cache_data)} raw files from processAllCfgs. Ingesting un-blanked properties...")
        
        for file_key, raw_payload in raw_cache_data.items():
            pruned_payload = {}
            for field_key, field_value in raw_payload.items():
                if field_key not in ["storage_reads", "storage_writes", "conditions_of_msg_sender", "functions_impacted"]:
                    pruned_payload[field_key] = field_value
            js_cfg_lookup_cache[file_key] = pruned_payload
    except Exception as err:
        print(f"Error executing trace processing optimization bounds: {str(err)}")
else:
    print("Critical Error: raw_trace_map.json swap file not found. Ensure processAllCfgs executes completely.")

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

# Ensure output workspace folder structure is generated cleanly
Path("./generated_cfgs").mkdir(exist_ok=True)
sentinode_holistic_map = {}

# [CONTINUED IN PART 3]
#BY GOD'S GRACE ALONE
# Continuation of sentinode_complete_core.py

# Primary loop running over all contracts tracked by the compilation unit environment
for contract in slither.contracts:
    # Retain the un-opinionated target filtering strategy from contract-summary/derived leaf models
    is_derived_leaf = contract in slither.contracts_derived
    is_abstract = getattr(contract, 'is_abstract', False)
    is_interface = contract.contract_kind == "interface"
    is_library = contract.contract_kind == "library"
    
    # --- CRITICAL FIX: LINEAGE ENFORCEMENT BOUNDARY CHECK ---
    # We inspect parent contract inheritance names to isolate forge-std framework modules.
    # This completely eliminates blunt string matching so that protocol contracts 
    # like 'SlitherTest' and 'SlitherRequireContract' are preserved natively.
    is_forge_framework_module = False
    if hasattr(contract, 'inheritance') and contract.inheritance:
        for parent_class in contract.inheritance:
            if parent_class.name in ["Test", "Script", "StdCheats", "CommonBase", "ScriptBase"]:
                is_forge_framework_module = True
                break
                
    file_path_abs = contract.source_mapping.filename.absolute if contract.source_mapping and contract.source_mapping.filename else ""
    is_forge_std_lib = "lib/forge-std/" in file_path_abs or "lib/ds-test/" in file_path_abs
    
    # Safely skip only true testing boilerplate systems while retaining real user target contracts
    if is_forge_framework_module or is_forge_std_lib or contract.is_test:
        continue

    # Determine explicit operational role tags for client workspace router selection phases
    if is_derived_leaf and not is_abstract and not is_interface and not is_library:
        ui_classification = "DEPLOYABLE_TARGET"
    elif is_interface or is_library:
        ui_classification = "INTERFACE_LIBRARY_STUB"
    elif is_abstract:
        ui_classification = "ABSTRACT_BASE_TEMPLATE"
    else:
        # Every inherited background OpenZeppelin base contract falls here cleanly instead of being dropped
        ui_classification = "INHERITED_LOGIC_LAYER"

    contract_name = contract.name
    
    # -------------------------------------------------------------------------
    # 1. INTEGRATED EXTRACTION: variable-order (With Layout Offset Mapping)
    # -------------------------------------------------------------------------
    variable_order_layout = []
    slot_index = 0
    
    # Access state_variables_ordered to capture elements across parent inheritance fields
    for var in contract.state_variables_ordered:
        if not (var.is_constant or var.is_immutable):
            try:
                slot, offset = contract.compilation_unit.storage_layout_of(contract, var)
            except Exception:
                slot, offset = "Unknown", "Unknown"
            variable_order_layout.append({
                "name": var.name,
                "canonical_name": var.canonical_name,
                "type": str(var.type),
                "slot": slot,
                "offset": offset,
                "state_type": "Storage",
                "inherited_from": var.contract.name if var.contract != contract else "Local"
            })
            slot_index += 1

    # -------------------------------------------------------------------------
    # 2. INTEGRATED EXTRACTION: function-summary Core Matrix
    # -------------------------------------------------------------------------
    (name, inheritance, var_summary, func_summaries, modif_summaries) = contract.get_summary()
    
    functions_manifest = []

# [CONTINUED IN PART 4 FOR FUNCTION SPLICING AND GRAPH CACHE MERGING]


#BY GOD'S GRACE ALONE
# Continuation of sentinode_complete_core.py

    for (
        _c_name, f_name, visi, modifiers, read, write, internal_calls, external_calls, cyclomatic_complexity
    ) in func_summaries:
        
        # Locate exact native Function object to bridge advanced structural attributes
        func_obj = next((f for f in contract.functions if f.full_name == f_name or f.name == f_name), None)
        
        # --- STEP 4: ENHANCED STORAGE READS & WRITES METRIC GENERATION ---
        storage_reads_enhanced = []
        storage_writes_enhanced = []
        
        if func_obj:
            # Generate enhanced reads mapping from Slither's state_variables_read objects
            for v_read in func_obj.state_variables_read:
                if hasattr(v_read, 'name') and hasattr(v_read, 'contract'):
                    defining_contract = v_read.contract.name
                    storage_reads_enhanced.append(f"{defining_contract}-{v_read.name}")
                    
            # Generate enhanced writes mapping from Slither's state_variables_written objects
            for v_write in func_obj.state_variables_written:
                if hasattr(v_write, 'name') and hasattr(v_write, 'contract'):
                    defining_contract = v_write.contract.name
                    storage_writes_enhanced.append(f"{defining_contract}-{v_write.name}")
                    
        # Apply standard sorting and de-duplication to enhanced structures
        storage_reads_enhanced = sorted(list(set(storage_reads_enhanced)))
        storage_writes_enhanced = sorted(list(set(storage_writes_enhanced)))

        # INTEGRATED EXTRACTION: entry-points Mapping Rules
        is_entry_point = False
        if func_obj:
            is_entry_point = (
                func_obj.visibility in ["public", "external"] and 
                not func_obj.view and 
                not func_obj.pure and 
                not func_obj.is_shadowed and
                not func_obj.is_constructor
            )

        # INTEGRATED EXTRACTION: require Printer via SlithIR Operations
        slithir_requires = []
        if func_obj:
            try:
                ops = func_obj.all_slithir_operations()
                matched_ops = [
                    ir for ir in ops 
                    if isinstance(ir, SolidityCall) and ir.function in require_or_assert_targets
                ]
                slithir_requires = [str(ir.node.expression) for ir in matched_ops if ir.node and ir.node.expression]
            except Exception:
                pass

        # INTEGRATED EXTRACTION: vars-and-auth (msg.sender checks & parent variable isolation)
        msg_sender_conditions = []
        state_variables_written_auth = []
        state_variables_written_auth_enhanced = []
        
        if func_obj:
            msg_sender_conditions = get_msg_sender_checks(func_obj)
            
            # Extract basic state variables written for authentication mapping arrays
            for v in func_obj.all_state_variables_written():
                if v.name:
                    state_variables_written_auth.append(v.name)
                    if hasattr(v, 'contract') and v.contract:
                        # Prepend parent declaring contract name to establish enhanced visibility paths
                        state_variables_written_auth_enhanced.append(f"{v.contract.name}-{v.name}")

        state_variables_written_auth = sorted(list(set(state_variables_written_auth)))
        state_variables_written_auth_enhanced = sorted(list(set(state_variables_written_auth_enhanced)))

        # INTEGRATED EXTRACTION: echidna Data Dependency / Invariant Fuzzing Relations
        impacts = []
        is_impacted_by = []
        impacts_enhanced = []
        is_impacted_by_enhanced = []
        constants_used = []
        constants_used_in_binary = defaultdict(list)
        
        if func_obj:
            # Map impacts and impact-dependencies based on state variable intersection vectors
            for other_func in contract.functions_entry_points:
                if other_func.name != func_obj.name and not other_func.is_shadowed:
                    other_reads = [v.name for v in other_func.all_state_variables_read()]
                    other_writes = [v.name for v in other_func.all_state_variables_written()]
                    
                    # Impacts rule calculation matching the required sibling-enhanced pattern
                    if any(r in other_reads for r in write):
                        func_signature = _get_name(other_func)
                        impacts.append(func_signature)
                        if hasattr(other_func, 'contract_declarer') and other_func.contract_declarer:
                            impacts_enhanced.append(f"{other_func.contract_declarer.name}-{func_signature}")
                            
                    # Is Impacted By rule calculation matching the required sibling-enhanced pattern
                    if any(r in other_writes for r in read):
                        func_signature = _get_name(other_func)
                        is_impacted_by.append(func_signature)
                        if hasattr(other_func, 'contract_declarer') and other_func.contract_declarer:
                            is_impacted_by_enhanced.append(f"{other_func.contract_declarer.name}-{func_signature}")

            # Extract local constant metrics for fuzzer seed parameters
            context_explored = set()
            context_explored.add(func_obj)
            try:
                _extract_constants_from_irs(func_obj.all_slithir_operations(), constants_used, constants_used_in_binary, context_explored)
            except Exception:
                pass

        # Format and group complete list schemas cleanly for JSON assembly parameters
        impacts = sorted(list(set(impacts)))
        is_impacted_by = sorted(list(set(is_impacted_by)))
        impacts_enhanced = sorted(list(set(impacts_enhanced)))
        is_impacted_by_enhanced = sorted(list(set(is_impacted_by_enhanced)))

        # --- CRITICAL O(1) CONSTANT TIME PRE-PRUNED CFG DEEP SPLICING ENGINE ---
        matched_cfg_deep_trace = None
        if func_obj:
            # Construct signature variables by re-extracting clean argument types
            sig_raw = func_obj.signature_str if hasattr(func_obj, 'signature_str') else ""
            param_types_str = sig_raw.split('(')[1].replace(')', '') if '(' in sig_raw else ""
            
            # Formulate the deterministic key fingerprint string handle
            target_cfg_filename = f".-{contract.name}-{func_obj.name}({param_types_str}).dot"
            
            # Query the pre-populated pruned lookup cache for an exact match.
            if target_cfg_filename in js_cfg_lookup_cache:
                matched_cfg_deep_trace = js_cfg_lookup_cache[target_cfg_filename]
            else:
                fallback_key = f".-{contract.name}-{func_obj.name}().dot"
                if fallback_key in js_cfg_lookup_cache:
                    matched_cfg_deep_trace = js_cfg_lookup_cache[fallback_key]
                else:
                    # Comprehensive scanning fallback routine to preserve mapping robustness
                    for available_key in js_cfg_lookup_cache.keys():
                        if available_key.startswith(f".-{contract.name}-{func_obj.name}("):
                            matched_cfg_deep_trace = js_cfg_lookup_cache[available_key]
                            break

        functions_manifest.append({
            "name": f_name,
            "visibility": visi,
            "is_state_changing_entry_point": is_entry_point,
            "modifiers": sorted(modifiers),
            "storage_reads": sorted(read),
            "storage_reads_enhanced": storage_reads_enhanced,
            "storage_writes": sorted(write),
            "storage_writes_enhanced": storage_writes_enhanced,
            "internal_calls": sorted(internal_calls),
            "external_calls": sorted(external_calls),
            "cyclomatic_complexity": cyclomatic_complexity,
            "require_printer_data": list(set(slithir_requires)),
            "msg_sender_auth_checks": list(set(msg_sender_conditions)),
            "vars_and_auth_matrix": {
                "state_variables_written": state_variables_written_auth,
                "state_variables_written_enhanced": state_variables_written_auth_enhanced,
                "has_auth_guards": len(msg_sender_conditions) > 0
            },
            "echidna_fuzzing_vectors": {
                "impacts_functions": impacts,
                "impacts_functions_enhanced": impacts_enhanced,
                "is_impacted_by_functions": is_impacted_by,
                "is_impacted_by_functions_enhanced": is_impacted_by_enhanced,
                "constants_discovered": [c._asdict() for c in list(set(constants_used)) if hasattr(c, '_asdict')],
                "binary_constants": {k: [c._asdict() for c in list(set(v)) if hasattr(c, '_asdict')] for k, v in constants_used_in_binary.items()}
            },
            # Verbatim trace block payload with internal duplicates cleanly omitted 
            "cfg_deep_trace": matched_cfg_deep_trace
        })

    # Pack full contract definition profile including deployment classification tags
    sentinode_holistic_map[contract_name] = {
        "contract_name": contract_name,
        "ui_classification": ui_classification,
        "is_most_derived_leaf": is_derived_leaf,
        "inheritance_chain": inheritance,
        "contract_variables_raw": var_summary,
        "storage_slot_layout": variable_order_layout,
        "functions": functions_manifest
    }

# [CONTINUED IN PART 5]
# BY GOD'S GRACE ALONE
# Continuation of sentinode_complete_core.py

# --- 8. STEP 8: LINEAGE-AWARE RUNTIME METRIC SYNCHRONIZATION ---
unique_source_files = set()
total_contracts_parsed = 0
classification_breakdown = defaultdict(int)

# Ingest baseline source records directly from the analyzer runtime engine context
if hasattr(slither, 'source_files'):
    for sf in slither.source_files:
        unique_source_files.add(str(sf))

# Process every active contract using structural lineage filtering to guarantee metric accuracy
for c in slither.contracts:
    # Match framework lineage conditions to filter out forge-std boilerplate safely
    is_forge_h = False
    if hasattr(c, 'inheritance') and c.inheritance:
        for p in c.inheritance:
            if p.name in ["Test", "Script", "StdCheats", "CommonBase", "ScriptBase"]:
                is_forge_h = True
                break
                
    f_path = c.source_mapping.filename.absolute if c.source_mapping and c.source_mapping.filename else ""
    is_forge_std_lib = "lib/forge-std/" in f_path or "lib/ds-test/" in f_path
    
    # Trigger drop rules exclusively on non-protocol framework artifacts using the fixed variable
    if is_forge_h or is_forge_std_lib or c.is_test:
        continue
        
    total_contracts_parsed += 1
    
    # Read the pre-mapped structural status configurations from Part 3
    is_leaf = c in slither.contracts_derived
    is_abs = getattr(c, 'is_abstract', False)
    is_inf = c.contract_kind == "interface"
    is_lib = c.contract_kind == "library"
    
    if is_leaf and not is_abs and not is_inf and not is_lib:
        final_ui_type = "DEPLOYABLE_TARGET"
    elif is_inf or is_lib:
        final_ui_type = "INTERFACE_LIBRARY_STUB"
    elif is_abs:
        final_ui_type = "ABSTRACT_BASE_TEMPLATE"
    else:
        final_ui_type = "INHERITED_LOGIC_LAYER"
        
    classification_breakdown[final_ui_type] += 1
    
    # Append the absolute production source file location map
    if c.source_mapping and c.source_mapping.filename:
        unique_source_files.add(c.source_mapping.filename.absolute)

# Synthesize the finalized interactive IDE package master manifest payload structure
final_ide_package_manifest = {
    "SENTINODE_RUN_METRICS": {
        "total_unique_source_files_compiled": len(unique_source_files),
        "total_contracts_discovered": total_contracts_parsed,
        "deployable_target_leafs": classification_breakdown["DEPLOYABLE_TARGET"],
        "abstract_base_templates": classification_breakdown["ABSTRACT_BASE_TEMPLATE"],
        "inherited_logic_layers": classification_breakdown["INHERITED_LOGIC_LAYER"],
        "interface_library_stubs": classification_breakdown["INTERFACE_LIBRARY_STUB"]
    },
    "CONTRACTS_BLUEPRINT_MAP": sentinode_holistic_map
}

# Write complete unfragmented bundle directly to the final JSON destination path
output_file_path = "./sentinode_master_manifest.json"
with open(output_file_path, "w") as f:
    json.dump(final_ide_package_manifest, f, indent=2)

print(json.dumps({
    "success": True, 
    "output_manifest": output_file_path,
    "metrics_synchronized": final_ide_package_manifest["SENTINODE_RUN_METRICS"]
}, indent=2))
