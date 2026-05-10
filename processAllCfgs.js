// BY GOD'S GRACE ALONE
const fs = require('fs');
const path = require('path');




function extractLayerOneTrace(cfgPath) {
    if (!fs.existsSync(cfgPath)) return { error: "File not found" };
    const dotContent = fs.readFileSync(cfgPath, 'utf8');

    // REGEX DEFINITIONS
    const nodeRegex = /(\d+)\[label="Node Type: ([A-Z_]+)\s+(\d+)([\s\S]*?)"\];/g;
    const internalCallRegex = /INTERNAL_CALL,\s*([^(\s,]+(?:\([^)]*\))?)/g;
    const modifierRegex = /MODIFIER_CALL,\s*([^(\s,]+(?:\([^)]*\))?)\(TMP/g;
    
    // Pattern 2: REVERT - Captures Name, Signatures, and Names
    const revertRegex = /revert\s+([^(]+)\(([^)]*)\)\(([^)]*)\)/g;
    
    // REFINED EVENT REGEX: Looks for the pattern between EXPRESSION: and IRs:
    // It accounts for newlines and grabs the clean Solidity-style call.
    const eventCaptureRegex = /EXPRESSION:\s*([\s\S]*?)\(([\s\S]*?)\)\s*IRs:/;

    const externalCallRegex = /HIGH_LEVEL_CALL,\s*dest:[^()]+\(([^)]+)\),\s*function:([^,]+),\s*arguments:\[([^\]]+)\]/g;

    let output = {
        "cfg": path.basename(cfgPath),
        "original_cfg_code": dotContent,
        "original_solidity_code": "",
        "contains_internal_calls_overall": false,
        "no_of_statements": 0,
        "modifiers_in_function": [],
        "reverts_in_function": [],
        "events_in_function": [],
        "inputs_into_function": [],
        "visibility": "",
        "returns_from_function": [],
        "is_a_view_function": "",
        "is_a_pure_function": "",
        "neither_pure_nor_view": "",
        "is_payable": "",
        "storage_reads": [],
        "storage_writes": [],
        "conditions_of_msg_sender": [],
        "functions_impacted": [],
        "first_level_tracing": []
    };

    let nodeMatch;
    while ((nodeMatch = nodeRegex.exec(dotContent)) !== null) {
        const [_, nodeId, nodeType, typeId, labelBody] = nodeMatch;
        output.no_of_statements++;
        const statementKey = `Statement_${nodeId}_Node_Type: ${nodeType} ${typeId}`;

        let sigs = [];
        let files = [];
        let extCalls = [];

        // --- 1. INTERNAL CALLS ---
        let callMatch;
        while ((callMatch = internalCallRegex.exec(labelBody)) !== null) {
            const sig = callMatch[1];
            sigs.push(sig);
            files.push(`${sig.replace(/\./g, '_')}.dot`);
        }
        if (sigs.length > 0) output.contains_internal_calls_overall = true;

        // --- 2. MODIFIERS ---
        let modMatch;
        while ((modMatch = modifierRegex.exec(labelBody)) !== null) {
            const fullModName = modMatch[1].trim();
            const parts = fullModName.split('.');
            const modObj = {};
            modObj[fullModName] = [
                parts[0], 
                parts[1] || parts[0],
                statementKey // Added as 3rd item in list
            ];
            output.modifiers_in_function.push(modObj);
        }

        // --- 3. REVERTS (With De-duplication) ---
        let revMatch;
        let seenRevertsInStatement = new Set(); // Local set for this node
        while ((revMatch = revertRegex.exec(labelBody)) !== null) {
            const [__, revName, inputs, names] = revMatch;
            const trimmedName = revName.trim();
            
            if (!seenRevertsInStatement.has(trimmedName)) {
                const safeSplit = (str) => str && str.trim() ? str.split(',').map(s => s.trim()) : [];
                const revObj = {};
                revObj[trimmedName] = {
                    "input_signatures": safeSplit(inputs),
                    "input_names": safeSplit(names),
                    "statement_found_in": statementKey
                };
                output.reverts_in_function.push(revObj);
                seenRevertsInStatement.add(trimmedName);
            }
        }

        // --- EVENT EXTRACTION (NEW STRATEGY) ---
        // We only trigger this if "Emit" exists in the IRs to ensure it's an event
        if (labelBody.includes("Emit ")) {
            const eventMatch = labelBody.match(eventCaptureRegex);
            if (eventMatch) {
                const eventName = eventMatch[1].trim();
                const cleanArgs = eventMatch[2].trim();
                
                const eveObj = {};
                eveObj[eventName] = {
                    "actual_event_call": `${eventName}(${cleanArgs})`,
                    "input_names": cleanArgs.split(',').map(n => n.trim()).filter(n => n !== ""),
                    "statement_found_in": statementKey
                };
                output.events_in_function.push(eveObj);
            }
        }

        // --- 7. EXTERNAL CALLS ---
        let extMatch;
        while ((extMatch = externalCallRegex.exec(labelBody)) !== null) {
            const [___, contractName, funcName, args] = extMatch;
            extCalls.push(`${contractName}-${funcName}, arguments:[${args}]`);
        }

        // --- ASSEMBLE STATEMENT ---
        const statementDetail = {};
        statementDetail[statementKey] = {
            "has_internal_calls": sigs.length > 0,
            "no_of_internal_calls": sigs.length,
            "identified_signatures": sigs,
            "identified_cfg_filenames": files,
            "has_external_calls": extCalls.length > 0,
            "external_call_details": extCalls
        };
        output.first_level_tracing.push(statementDetail);
    }

    return output;
}





function processHolisticSchema(rootDir) {
    const generatedDir = path.resolve(rootDir, 'generated_cfgs');
    const absoluteRoot = path.resolve(rootDir);

    // 1. Organize Project Structure
    if (!fs.existsSync(generatedDir)) {
        console.log(`Creating directory: ${generatedDir}`);
        fs.mkdirSync(generatedDir, { recursive: true });
    }

    // Move all .dot files from root to generated_cfgs
    console.log(`Scanning root: ${absoluteRoot} for .dot files...`);
    const files = fs.readdirSync(absoluteRoot);
    let movedCount = 0;

    files.forEach(file => {
        if (file.endsWith('.dot')) {
            const oldPath = path.join(absoluteRoot, file);
            const newPath = path.join(generatedDir, file);
            try {
                fs.renameSync(oldPath, newPath);
                movedCount++;
            } catch (err) {
                console.error(`Failed to move ${file}: ${err.message}`);
            }
        }
    });
    console.log(`Successfully moved ${movedCount} files to /generated_cfgs.`);

    // 2. Holistic Logic Extraction
    const holisticObject = {};
    const cfgFiles = fs.readdirSync(generatedDir);

    cfgFiles.forEach(filename => {
        if (filename.endsWith('.dot')) {
            const cfgPath = path.join(generatedDir, filename);
            
            const extractedTrace = extractLayerOneTrace(cfgPath)

            holisticObject[filename] = extractedTrace
        }
    });

    return holisticObject;
}




// EXECUTION 
const SENTINODE_MAP = processHolisticSchema('./');
console.log(`Total Holistic Object Keys: ${Object.keys(SENTINODE_MAP).length}`);


const targetFile = '.-AccessControl-_checkRole(bytes32).dot';
// To print a specific file's full logic data:
console.log(`--- DEEP TRACE FOR: ${targetFile} ---`);
console.log(JSON.stringify(SENTINODE_MAP[targetFile], null, 2));





