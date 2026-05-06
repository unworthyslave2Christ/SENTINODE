// BY GOD'S GRACE ALONE
const fs = require('fs');
const path = require('path');

const DOT_FOLDER = './cfgs';
const OUTPUT_FOLDER = './sentinode_traces';

function getTargetFileName(callString) {
    const parts = callString.split('.');
    const files = fs.readdirSync(DOT_FOLDER);
    const pattern = `-${parts[0]}-${parts[1]}(`;
    return files.find(f => f.includes(pattern)) || null;
}

function generateDeepTrace(fileName, prefix = "1", visited = new Set()) {
    const filePath = path.join(DOT_FOLDER, fileName);
    if (!fs.existsSync(filePath) || visited.has(fileName)) return "";
    visited.add(fileName);

    let dotContent = fs.readFileSync(filePath, 'utf8');
    const bodyMatch = dotContent.match(/digraph\s*\{([\s\S]*)\}/);
    if (!bodyMatch) return "";
    let body = bodyMatch[1];

    // 1. Rename all Nodes first to ensure namespacing
    body = body.replace(/(\d+)\[label="/g, `"${prefix}_$1"[label="`);

    // 2. Fix Edges (Standard and Conditional)
    // Matches: 1 -> 2 or 1 -> 2 [label="True"]
    body = body.replace(/(\d+)\s*->\s*(\d+)/g, `"${prefix}_$1" -> "${prefix}_$2"`);

    // 3. Process Internal Calls and Stitch Subgraphs
    const internalCallPattern = /INTERNAL_CALL, ([\w\.]+)\(/g;
    const nodePattern = /"(\1_\d+)"\[label="(.*?)"\]/gs; // Matches our newly renamed nodes

    body = body.replace(/"(\d+_\d+)"\[label="(.*?)"\]/g, (match, fullId, label) => {
        const nodeId = fullId.split('_').pop(); 
        const indexMatch = label.match(/(EXPRESSION|IF|RETURN|OTHER_ENTRYPOINT) (\d+)/);
        const expIndex = indexMatch ? indexMatch[2] : nodeId;
        
        let updatedLabel = label;
        let callCount = 0;
        let subGraphs = "";
        let callMatch;

        while ((callMatch = internalCallPattern.exec(label)) !== null) {
            callCount++;
            const coordinate = `${prefix}_${expIndex}_${callCount}`;
            const targetFile = getTargetFileName(callMatch[1]);

            updatedLabel = updatedLabel.replace(callMatch[0], `INTERNAL_CALL [Branch ${coordinate}], ${callMatch[1]}(`);

            if (targetFile) {
                const subBody = generateDeepTrace(targetFile, coordinate, new Set(visited));
                subGraphs += `\n/* Branch ${coordinate} */\n${subBody}\n`;
                subGraphs += `"${fullId}" -> "${coordinate}_0" [label="DEEP TRACE: ${coordinate}", color=blue, style=dashed, fontcolor=blue];\n`;
            }
        }
        return `"${fullId}" [label="${updatedLabel}"]\n${subGraphs}`;
    });

    return body;
}

// RUNNER (Make sure targetEntry matches your file exactly)
const targetEntry = ".-AccessControl-revokeRole(bytes32,address).dot"; 
const fullBody = generateDeepTrace(targetEntry);
const finalDot = `digraph SENTINODE_DEEP_TRACE {\nrankdir=LR;\nnode [shape=box, style=filled, color=lightgrey, fontname="Courier"];\n${fullBody}\n}`;
fs.writeFileSync(path.join(OUTPUT_FOLDER, 'DeepTrace_Corrected.dot'), finalDot);
