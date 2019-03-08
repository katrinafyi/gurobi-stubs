import gurobipy

import inspect
from typing import Any
from collections import namedtuple 
import time
import sys


TypedObject = namedtuple('TypedObject', 'name type')

# pep-257
def trim(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return trimmed 

def superclass_names(cls: Any) -> str:
    out = []
    for sup in cls.__bases__:
        out.append(sup.__name__)
    return ', '.join(out)
# time.sleep(5)

def signature(func, method=False) -> str:
    try:
        return str(inspect.signature(func))
    except Exception as e:
        doc = (func.__doc__ or '').strip()
        if doc.startswith('ROUTINE:'):
            sig = doc.replace('ROUTINE:', '').strip().split(')')[0].strip() + ')'
            sig = '('+ ('self, ' if method else '')+ '('.join(sig.split('(')[1:])
            if sig == '(self, )': sig = '(self)'
            return sig 
        raise e

def parse_attributes():
    indent_level = lambda s: len(s) - len(s.lstrip())

    doc = gurobipy.GRB.Attr.__doc__
    mapping = {
        'General model attributes': gurobipy.Model,
        'Variable attributes': gurobipy.Var,
        'Constraint attributes': gurobipy.Constr,
        'SOS': gurobipy.SOS,
        'Quadratic constraint attributes': gurobipy.QConstr,
        'GenConstr': gurobipy.GenConstr,
    }
    base_indent = None
    b = None
    obj = None 

    output = {}

    for line in doc.split('\n'):
        line = line.rstrip() 
        if not line: continue 

        if base_indent is None:
            base_indent = indent_level(line)
            b = line[:base_indent]
        elif indent_level(line) == base_indent:
            matched = [obj for text, obj in mapping.items() if line.strip().startswith(text) and line.endswith(':')]
            if matched:
                obj = matched[0]
                output[obj] = []
            else:
                obj = None
        elif indent_level(line) == base_indent + 2 and obj:
            name, *rest = line.strip().split(':')
            comment = ':'.join(rest).strip()
            output[obj].append(name + ' = ...')
            output[obj].append('"""' + comment + '"""')
        elif indent_level(line) > base_indent + 2 and obj:
            if output[obj]:
                output[obj][-1] = output[obj][-1].rstrip('"""') + ' ' + line.strip() + '"""'
    return output
        

attributes = parse_attributes()

blacklist = ['__name__', '__doc__', '__package__', '__loader__',
'__spec__', '__path__', '__file__', '__cached__', '__builtins__',
'__doc__', '__hash__', '__dict__', '__module__']



def main(root, indent=0, vscode=0) -> str:
    output = []
    i = indent*' '

    def write(x: Any) -> None:
        output.append(i+x)

    def write_doc(x: Any) -> None:
        if x.__doc__:
            output.append(i + '    """')
            p = '' if x.__doc__.strip().startswith('ROUTINE:') else '    '
            if vscode:
                doc = trim(x.__doc__)
                output.extend(doc)
            else:
                output.extend(i+p+y for y in x.__doc__.split('\n'))
            output.append(i + '    """')

    def write_func(name, obj, is_method=False):
        first_arg = "self, " if is_method else ""

        decorator = ''
        if obj.__doc__:
            if obj.__doc__ == classmethod.__doc__:
                decorator = '@classmethod'
                first_arg = 'cls, '
            elif obj.__doc__ == staticmethod.__doc__:
                decorator = '@staticmethod'
                first_arg = ''

        if decorator:
            write(decorator)
        try:
            write(f'def {name}{(signature(obj, is_method))}:')
        except (ValueError, TypeError):
            write(f'def {name}({first_arg}*args, **kwargs) -> Any:')
        if not decorator:
            write_doc(obj)
        write(f'    ...')

    for name, obj in root.__dict__.items():
        #print(name)
        if inspect.ismodule(obj) or name in blacklist: # ignore modules
            continue 
        elif inspect.isclass(obj):
            write(f'class {name}({superclass_names(obj)}):')
            write_doc(obj)
            output.extend(main(obj, indent+4, vscode))
        elif inspect.ismethod(obj) or inspect.ismethoddescriptor(obj):
            write_func(name, obj, True)
        elif inspect.isfunction(obj):
            write_func(name, obj)
        elif type(obj).__name__ == 'builtin_function_or_method':
            write_func(name, obj)
        else:
            if type(obj).__name__ not in ('builtin_function_or_method', 'getset_descriptor', 'NoneType', '_abc_data'):
                write(f'{name}: {type(obj).__name__} = ...')
    if root in attributes:
        output.extend(i+x for x in attributes[root])
    
    return output

def make_stub(vscode=False):
    return '\n'.join(
        ['from typing import Any', 
        'from io import TextIOBase as _TextIOBase', 
        ''] 
        + main(gurobipy, vscode=vscode)
    ).replace(', /', '')


if __name__ == "__main__":
    #parse_attributes()
    # print(attributes)
    with open('gurobipy.pyi', 'w') as f:
        f.write(make_stub(vscode=False))
    with open('gurobipy_vscode.pyi', 'w') as f:
        f.write(make_stub(vscode=True))