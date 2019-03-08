# gurobi-stubs
Stub .pyi files for Gurobi. Used for autocomplete in VS Code.

### Usage
VS Code uses the Jedi completion library by default, which doesn't support 
.pyi files. Set 

    "python.jediEnabled": false

in any settings file. Then, download the stub file and place it where VS Code
can find it.

gurobipy_vscode.pyi is identical but without indentation on docstrings, 
because VS Code doesn't correctly trim docstring indentation...