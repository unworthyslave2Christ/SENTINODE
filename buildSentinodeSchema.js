const fs = require('fs');
const path = require('path');

/**
 * SENTINODE: Logic Extraction Engine
 * Layer 1 Deep Trace Generator
 */
function extractLayerOneTrace(cfgPath) {
    // 1. Extract content based off the corresponding cfg path
    if (!fs.existsSync(cfgPath)) return { error: "File not found" };
    const dotContent = fs.readFileSync(cfgPath, 'utf8');
    
    // Regex Definitions
    const nodeRegex = /(\d+)\[label="Node Type: ([A-Z_]+)\s+(\d+)([\s\S]*?)"\];/g;
    const internalCallRegex = /INTERNAL_CALL,\s*([^(\s,]+(?:\([^)]*\))?)/g;

    // Step 1: Initialize main JSON structure
    let output = {
        "cfg": path.basename(cfgPath),
        "contains_internal_calls_overall": false, // Initial value
        "no_of_statements": 0,
        "first_level_tracing": []
    };

    let nodeMatch;
    // Step 1 & 2: Find statements and simultaneously check for internal calls
    while ((nodeMatch = nodeRegex.exec(dotContent)) !== null) {
        const [_, nodeId, nodeType, typeId, labelBody] = nodeMatch;
        output.no_of_statements++;

        let signatures = [];
        let filenames = [];
        let callMatch;

        // Step 3: Match INTERNAL CALLS using refined pattern
        while ((callMatch = internalCallRegex.exec(labelBody)) !== null) {
            const sig = callMatch[1]; // Signature: AccessControl.hasRole(bytes32,address)
            signatures.push(sig);
            // Contract-prefixed names (identical results from pattern matching)
            filenames.push(`${sig.replace(/\./g, '_')}.dot`);
        }

        const hasCalls = signatures.length > 0;
        
        // Update overall flag if any statement has a call
        if (hasCalls) output.contains_internal_calls_overall = true;

        // Step 4: Construct the first_level_tracing list item
        const nodeKey = `Statement_${nodeId}_Node_Type: ${nodeType} ${typeId}`;
        const statementDetail = {};
        statementDetail[nodeKey] = {
            "has_internal_calls": hasCalls,
            "no_of_internal_calls": signatures.length,
            "identified_signatures": signatures,
            "identified_cfg_filenames": filenames
        };

        output.first_level_tracing.push(statementDetail);
    }

    return output;
}

function enhanceParentCFG(parentPath, layerOneJson, cfgsDir) {
    if (!layerOneJson.contains_internal_calls_overall) {
        console.log("No internal calls found. Returning original.");
        return fs.readFileSync(parentPath, 'utf8');
    }

    let parentDot = fs.readFileSync(parentPath, 'utf8').trim();
    // Use a non-greedy replace for the final brace
    let enhancedDot = parentDot.substring(0, parentDot.lastIndexOf("}"));

    layerOneJson.first_level_tracing.forEach((statementWrapper) => {
        const nodeKey = Object.keys(statementWrapper)[0];
        const nodeData = statementWrapper[nodeKey];

        if (nodeData.has_internal_calls) {
            // Regex to grab just the ID number from the statement key
            const originNodeId = nodeKey.match(/Statement_(\d+)/)[1];

            nodeData.identified_cfg_filenames.forEach((targetFilename) => {
                // Ensure we are looking in the correct directory
                const targetPath = path.join(cfgsDir, targetFilename);

                if (fs.existsSync(targetPath)) {
                    let childDot = fs.readFileSync(targetPath, 'utf8').trim();
                    const branchTag = targetFilename.replace(/^[./-]+/, "").replace(".dot", "");

                    // Extract logic between the outermost digraph braces
                    const firstBrace = childDot.indexOf("{") + 1;
                    const lastBrace = childDot.lastIndexOf("}");
                    let childBody = childDot.substring(firstBrace, lastBrace).trim();

                    if (childBody) {
                        // 1. Inject the called CFG content
                        enhancedDot += `\n\n  /* Deep Trace: ${branchTag} */\n`;
                        enhancedDot += `  ${childBody}\n`;

                        // 2. Add the Curvy Branch
                        // Points from the call node to Entry Node 0
                        enhancedDot += `  ${originNodeId} -> 0 [label="${branchTag}", style="curved", color="orange"];\n`;
                        console.log(`Successfully enhanced with ${branchTag}`);
                    }
                } else {
                    console.log(`Skipped: File not found at ${targetPath}`);
                }
            });
        }
    });

    enhancedDot += "\n}";
    return enhancedDot;
}


// Example usage
const targetFile = './.-AccessControl-_checkRole(bytes32,address).dot'

const firstLayer = extractLayerOneTrace(targetFile);
console.log(JSON.stringify(firstLayer, null, 2));

const result = enhanceParentCFG(targetFile, data, "./");

console.log("\n--- RESULTING DOT ---\n");
console.log(result);




