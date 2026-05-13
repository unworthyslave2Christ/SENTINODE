#BY GOD'S GRACE ALONE
import json
import sys
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
        value_type = ir.type.type if isinstance(ir, TypeConversion) and isinstance(ir.type, TypeAlias) else (ir.type if isinstance(ir, TypeConversion) else var_read.type)
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
            value_type = ir.type.type if isinstance(ir.type, TypeAlias) else ir.type
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

# [CONTINUED IN NEXT BLOCK]
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

try:
    slither = Slither('.')
except Exception as e:
    print(json.dumps({"error": f"Compilation failed: {str(e)}"}))
    sys.exit(1)

# Ensure output workspace folder structure is generated cleanly
Path("./generated_cfgs").mkdir(exist_ok=True)

sentinode_holistic_map = {}

# Primary loop running over fully derived top-level smart contract scopes
for contract in slither.contracts_derived:
    if (
        contract.is_test or 
        contract.is_from_dependency() or 
        contract.is_interface or 
        contract.is_library or 
        contract.is_abstract
    ):
        continue

    contract_name = contract.name
    
    # -------------------------------------------------------------------------
    # 1. INTEGRATED EXTRACTION: variable-order
    # -------------------------------------------------------------------------
    variable_order_layout = []
    slot_index = 0
    for var in contract.state_variables_ordered:
        if not (var.is_constant or var.is_immutable):
            try:
                slot, offset = contract.compilation_unit.storage_layout_of(contract, var)
            except Exception:
                slot, offset = "Unknown", "Unknown"
            variable_order_layout.append({
                "name": var.name,
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
    (name, inheritance, var, func_summaries, modif_summaries) = contract.get_summary()
    
    functions_manifest = []
    
    for (
        _c_name, f_name, visi, modifiers, read, write, internal_calls, external_calls, cyclomatic_complexity
    ) in func_summaries:
        
        # Locate exact native Function object to bridge advanced structural attributes
        func_obj = next((f for f in contract.functions if f.full_name == f_name or f.name == f_name), None)
        
        # 3. INTEGRATED EXTRACTION: entry-points Mapping Rules
        is_entry_point = False
        if func_obj:
            is_entry_point = (
                func_obj.visibility in ["public", "external"] and 
                not func_obj.view and 
                not func_obj.pure and 
                not func_obj.is_shadowed and
                not func_obj.is_constructor
            )

        # 4. INTEGRATED EXTRACTION: require Printer via SlithIR Operations
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

        # 5. INTEGRATED EXTRACTION: vars-and-auth (msg.sender checks)
        msg_sender_conditions = []
        state_variables_written_auth = []
        if func_obj:
            state_variables_written_auth = [v.name for v in func_obj.all_state_variables_written() if v.name]
            msg_sender_conditions = get_msg_sender_checks(func_obj)

        # 6. INTEGRATED EXTRACTION: echidna Data Dependency / Invariant Fuzzing Relations
        impacts = []
        is_impacted_by = []
        constants_used = []
        constants_used_in_binary = defaultdict(list)
        
        if func_obj:
            # Map impacts and impact-dependencies based on state variable intersection vectors
            for other_func in contract.functions_entry_points:
                if other_func.name != func_obj.name and not other_func.is_shadowed:
                    # Impacts rule calculation
                    if any(r in [v.name for v in other_func.all_state_variables_read()] for r in write):
                        impacts.append(_get_name(other_func))
                    # Is Impacted By rule calculation
                    if any(r in [v.name for v in other_func.all_state_variables_written()] for r in read):
                        is_impacted_by.append(_get_name(other_func))

            # Extract local constant metrics for fuzzing seed parameters
            context_explored = set()
            context_explored.add(func_obj)
            try:
                _extract_constants_from_irs(func_obj.all_slithir_operations(), constants_used, constants_used_in_binary, context_explored)
            except Exception:
                pass

        functions_manifest.append({
            "name": f_name,
            "visibility": visi,
            "is_state_changing_entry_point": is_entry_point,
            "modifiers": sorted(modifiers),
            "storage_reads": sorted(read),
            "storage_writes": sorted(write),
            "internal_calls": sorted(internal_calls),
            "external_calls": sorted(external_calls),
            "cyclomatic_complexity": cyclomatic_complexity,
            "require_printer_data": list(set(slithir_requires)),
            "msg_sender_auth_checks": list(set(msg_sender_conditions)),
            "vars_and_auth_matrix": {
                "state_variables_written": sorted(state_variables_written_auth),
                "has_auth_guards": len(msg_sender_conditions) > 0
            },
            "echidna_fuzzing_vectors": {
                "impacts_functions": list(set(impacts)),
                "is_impacted_by_functions": list(set(is_impacted_by)),
                "constants_discovered": [c._asdict() for c in list(set(constants_used)) if hasattr(c, '_asdict')],
                "binary_constants": {k: [c._asdict() for c in list(set(v)) if hasattr(c, '_asdict')] for k, v in constants_used_in_binary.items()}
            }
        })

    # Pack full contract definition profile node values
    sentinode_holistic_map[contract_name] = {
        "contract_name": contract_name,
        "inheritance_chain": inheritance,
        "contract_variables_raw": var,
        "storage_slot_layout": variable_order_layout,
        "functions": functions_manifest
    }

# Write complete unfragmented O(1) Manifest out directly to JSON file destination path
output_file_path = "./sentinode_master_manifest.json"
with open(output_file_path, "w") as f:
    json.dump(sentinode_holistic_map, f, indent=2)

print(json.dumps({"success": True, "output_manifest": output_file_path}))
