// Important commands
slither . --print contract-summary,function-summary --json sentinode_complete_map.json
slither . --print function-summary --json sentinode_function_summary_map.json
slither . --print contract-summary --json sentinode_contract_summary_map.json

//TODO What do the results for this command mean for the phase 1 of the project, is phase 1 done and/or what are the next steps to take?
//TODO Are there more relevant slither commands?


// For seeing vulnerability issues
slither . --json sentinode_report.json


unworthyslavetochrist@DESKTOP-KKCGIOJ:~/foundry-2026-forCHRISTALONE/foundry-cross-chain-rebase-token$ slither . --list-printers
+-----+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Num | Printer           | What it Does                                                                                                                                                                      |
+-----+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 1   | call-graph        | Export the call-graph of the contracts to a dot file                                                                                                                              |
| 2   | cfg               | Export the CFG of each functions                                                                                                                                                  |
| 3   | cheatcode         |  Print the usage of (Foundry) cheatcodes in the code. For the complete list of Cheatcodes, see https://book.getfoundry.sh/cheatcodes/                                             |
| 4   | ck                | Chidamber and Kemerer (CK) complexity metrics and related function attributes                                                                                                     |
| 5   | constructor-calls | Print the constructors executed                                                                                                                                                   |
| 6   | contract-summary  | Print a summary of the contracts                                                                                                                                                  |
| 7   | data-dependency   | Print the data dependencies of the variables                                                                                                                                      |
| 8   | declaration       | Prototype showing the source code declaration, implementation and references of the contracts objects                                                                             |
| 9   | dominator         | Export the dominator tree of each functions                                                                                                                                       |
| 10  | echidna           | Export Echidna guiding information                                                                                                                                                |
| 11  | entry-points      | Print all the state-changing entry point functions and their variables of the contracts                                                                                           |
| 12  | evm               | Print the evm instructions of nodes in functions                                                                                                                                  |
| 13  | function-id       | Print the keccak256 signature of the functions                                                                                                                                    |
| 14  | function-summary  | Print a summary of the functions                                                                                                                                                  |
| 15  | halstead          | Computes the Halstead complexity metrics for each contract                                                                                                                        |
| 16  | human-summary     | Print a human-readable summary of the contracts                                                                                                                                   |
| 17  | inheritance       | Print the inheritance relations between contracts                                                                                                                                 |
| 18  | inheritance-graph | Export the inheritance graph of each contract to a dot file                                                                                                                       |
| 19  | loc               | Count the total number lines of code (LOC), source lines of code (SLOC), and comment lines of code (CLOC) found in source files (SRC), dependencies (DEP), and test files (TEST). |
| 20  | martin            | Martin agile software metrics (Ca, Ce, I, A, D)                                                                                                                                   |
| 21  | modifiers         | Print the modifiers called by each function                                                                                                                                       |
| 22  | not-pausable      | Print functions that do not use whenNotPaused                                                                                                                                     |
| 23  | require           | Print the require and assert calls of each function                                                                                                                               |
| 24  | slithir           | Print the slithIR representation of the functions                                                                                                                                 |
| 25  | slithir-ssa       | Print the slithIR representation of the functions                                                                                                                                 |
| 26  | variable-order    | Print the storage order of the state variables                                                                                                                                    |
| 27  | vars-and-auth     | Print the state variables written and the authorization of the functions                                                                                                          |
+-----+-------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Printers:
  --print PRINTERS_TO_RUN
                        Comma-separated list of contract information printers, available printers: cfg, ck, cheatcode,
                        constructor-calls, contract-summary, data-dependency, declaration, dominator, echidna, function-
                        id, function-summary, halstead, loc, martin, modifiers, call-graph, evm, entry-points, human-
                        summary, inheritance, inheritance-graph, slithir, slithir-ssa, not-pausable, vars-and-auth,
                        require, variable-order
  --include-interfaces  Include interfaces from inheritance-graph printer
  --list-printers       List available printers




// Granting permissions to a different user (linux-ubuntu env)
sudo chown -R $USER:$USER /home/unworthyslavetochrist/foundry-2026-forCHRISTALONE/
chmod -R 755 /home/unworthyslavetochrist/foundry-2026-forCHRISTALONE/

If you ran the chown and chmod commands and you are still seeing Read-only file system (os error 30), this isn't a simple permission issue—your Linux kernel has likely locked the entire hard drive/partition to prevent data corruption. 
This often happens on WSL or Linux if there was a sudden crash or a hardware "hiccup." No matter what commands you run, the OS will not let anything write to that disk until it's reset.
How to break the "Read-Only" Lock:
If you are on WSL (Windows Subsystem for Linux):
The easiest way is to restart the WSL engine from your Windows PowerShell:
Close your terminal.
Open PowerShell as Administrator and run:
powershell
wsl --shutdown
