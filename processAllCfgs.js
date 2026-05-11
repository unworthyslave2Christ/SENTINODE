// BY GOD'S GRACE ALONE
const fs = require('fs');
const path = require('path');


function extractLayerOneTrace(cfgPath) {
    if (!fs.existsSync(cfgPath)) return { error: "File not found" };
    const dotContent = fs.readFileSync(cfgPath, 'utf8');

    // REGEX DEFINITIONS
    const nodeRegex = /(\d+)\[label="Node Type: ([A-Z_]+)\s+(\d+)([\s\S]*?)"\];/g;
    const internalCallRegex = /INTERNAL_CALL,\s*([^(\s,]+(?:\([^)]*\))?)/g;
    // Captures from MODIFIER_CALL up to the first (TMP or the final empty ()
    const modifierRegex = /MODIFIER_CALL,\s*([^)]+(?:\([^)]*\))?)\(/g;

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
            files.push(`${sig.replace(/\./g, '-')}.dot`);
        }
        if (sigs.length > 0) output.contains_internal_calls_overall = true;

        // --- 2. MODIFIERS ---
        let modMatch;
        while ((modMatch = modifierRegex.exec(labelBody)) !== null) {
            let fullModName = modMatch[1].trim(); // e.g. "Ownable.onlyOwner()"
            
            // Clean up empty parens if they exist at the end for the key
            const cleanKey = fullModName.replace(/\(\)$/, ""); 
            const parts = fullModName.split('.');
            
            const modObj = {};
            modObj[fullModName] = [
                parts[0],              // Contract Name: "Ownable"
                parts[1] || parts[0],  // Pure Signature: "onlyOwner()"
                statementKey           // Anchored Statement
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
    const SENTINODE_MAP = {};
    const cfgFiles = fs.readdirSync(generatedDir);

    const flattenedPath = path.resolve(rootDir, 'crytic-export/flattening/export.sol');
    if (!fs.existsSync(flattenedPath)) {
        console.error("Critical: Flattened source 'export.sol' not found.");
        return {};
    }
    const flattenedSource = fs.readFileSync(flattenedPath, 'utf8');
    
    cfgFiles.forEach(filename => {
        if (filename.endsWith('.dot')) {
            const cfgPath = path.join(generatedDir, filename);
            const output = extractLayerOneTrace(cfgPath);

            const nameMatch = filename.match(/\.-([^-]+)-([^(]+)\(([^)]*)\)/);
            
            if (nameMatch) {
                const contractName = nameMatch[1];
                const functionName = nameMatch[2];
                const rawFingerprint = nameMatch[3];
                const expectedTypes = rawFingerprint ? rawFingerprint.split(',').map(t => t.trim()).filter(t => t !== "") : [];

                // 1. Isolate the specific Contract block (Stop at next 'contract' or 'interface' or 'library')
                const contractRegex = new RegExp(`contract\\s+${contractName}[\\s\\S]*?(?=\\ncontract|\\ninterface|\\nlibrary|$)`, 'g');
                const contractMatch = contractRegex.exec(flattenedSource);
                const contractBlock = contractMatch ? contractMatch[0] : null;

                if (contractBlock) {
                    // 2. Locate Function Header
                    const funcHeaderRegex = new RegExp(`function\\s+${functionName}\\s*\\(([^)]*)\\)[^{]*{`, 'g');
                    
                    let headerMatch;
                    while ((headerMatch = funcHeaderRegex.exec(contractBlock)) !== null) {
                        const rawParams = headerMatch[1];
                        const paramEntries = rawParams.split(',').map(p => p.trim()).filter(p => p !== "");
                        const foundTypes = paramEntries.map(p => p.split(/\s+/)[0]); // Get only the first word (the type)

                        // 3. Exact Type Match for Overloads
                        if (JSON.stringify(foundTypes) === JSON.stringify(expectedTypes)) {
                            
                            // 4. PRECISE BRACE COUNTING
                            let openBraces = 0;
                            let cursor = headerMatch.index;
                            let bodyFound = false;
                            let bodyEnd = cursor;

                            // Start scanning from the headerMatch index
                            while (cursor < contractBlock.length) {
                                if (contractBlock[cursor] === '{') {
                                    openBraces++;
                                    bodyFound = true;
                                }
                                if (contractBlock[cursor] === '}') {
                                    openBraces--;
                                }
                                // Once we've opened at least one brace and returned to 0, the function ends
                                if (bodyFound && openBraces === 0) {
                                    bodyEnd = cursor + 1;
                                    break;
                                }
                                cursor++;
                            }

                            const fullSource = contractBlock.substring(headerMatch.index, bodyEnd);
                            output.original_solidity_code = fullSource.trim();

                            // 5. Populate Metadata
                            output.inputs_into_function = [];
                            paramEntries.forEach(entry => {
                                const parts = entry.split(/\s+/);
                                const pName = parts.pop();
                                const pType = parts.join(' ');
                                let inputObj = {};
                                inputObj[pName] = pType;
                                output.inputs_into_function.push(inputObj);
                            });

                            const headerOnly = fullSource.split('{')[0];
                            output.is_a_view_function = /\bview\b/.test(headerOnly);
                            output.is_a_pure_function = /\bpure\b/.test(headerOnly);
                            output.is_payable = /\bpayable\b/.test(headerOnly);
                            output.is_virtual = /\bvirtual\b/.test(headerOnly);
                            output.is_override = /\boverride\b/.test(headerOnly);
                            output.neither_pure_nor_view = !(output.is_a_view_function || output.is_a_pure_function);

                            const visMatch = headerOnly.match(/\b(public|external|internal|private)\b/);
                            output.visibility = visMatch ? visMatch[0] : "";

                            const returnsMatch = headerOnly.match(/returns\s*\(([^)]*)\)/);
                            if (returnsMatch) {
                                output.returns_from_function = returnsMatch[1].split(',').map(r => r.trim());
                            }

                            break; // Stop searching once exact overload is matched
                        }
                    }
                }
            }
            SENTINODE_MAP[filename] = output;
        }
    });




    return SENTINODE_MAP;
}



// EXECUTION 
const SENTINODE_MAP = processHolisticSchema('./');
console.log(`Total Holistic Object Keys: ${Object.keys(SENTINODE_MAP).length}`);


const targetFile = '.-RebaseToken-mint(address,uint256).dot';
// To print a specific file's full logic data:
console.log(`--- DEEP TRACE FOR: ${targetFile} ---`);
console.log(JSON.stringify(SENTINODE_MAP[targetFile], null, 2));





