"""Experiment A: evaluate Python against visible rows in an isolated, key-free worker."""
import ast
import contextlib
import ctypes
import io
import json
import math
from pathlib import Path
import resource
import statistics
import subprocess
import sys

ALLOWED = {'pandas', 'numpy', 'math', 'statistics'}


def validate(code):
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(x.name not in ALLOWED for x in node.names):
            raise ValueError('only pandas/numpy/math/statistics imports are available')
        if isinstance(node, ast.ImportFrom) and (node.level or node.module not in ALLOWED):
            raise ValueError('unsupported import')
        if isinstance(node, (ast.Import, ast.ImportFrom)) and any(x.name.startswith('_') or (x.asname or '').startswith('__') for x in node.names):
            raise ValueError('private import aliases are unavailable')
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
            raise ValueError('private attributes are unavailable')
        if isinstance(node, ast.Name) and node.id.startswith('__'):
            raise ValueError('private names are unavailable')
    return tree


def execute(rows_csv, code):
    try:
        validate(code)
        result = subprocess.run([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--worker'],
                                input=json.dumps({'rows_csv': rows_csv, 'code': code}), text=True,
                                capture_output=True, timeout=18,
                                env={'PATH': '/usr/bin:/bin', 'OPENBLAS_NUM_THREADS': '1', 'TZ': 'UTC'})
        if result.returncode:
            raise RuntimeError('isolated worker failed: ' + result.stderr[-300:])
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {'output': 'ERROR: visible-row computation timed out', 'isolation': 'seatbelt-subprocess', 'error': True}
    except (ValueError, SyntaxError) as exc:
        return {'output': 'ERROR: ' + str(exc)[:400], 'isolation': 'rejected-before-execution', 'error': True}


def restrict():
    roots = {sys.prefix, sys.base_prefix, '/System/Library', '/usr/lib'}
    reads = ' '.join(f'(subpath {json.dumps(x)})' for x in sorted(roots))
    policy = f'(version 1)(deny default)(allow sysctl-read)(allow file-read* {reads})'
    lib = ctypes.CDLL('/usr/lib/libsandbox.dylib')
    lib.sandbox_init.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p)]
    error = ctypes.c_char_p()
    if lib.sandbox_init(policy.encode(), 0, ctypes.byref(error)):
        raise RuntimeError('Unable to install visible-row sandbox')


def worker():
    import pandas as pd
    import numpy as np
    packet = json.load(sys.stdin)
    df = pd.read_csv(io.StringIO(packet['rows_csv']))
    tree = validate(packet['code'])
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    restrict()
    def importer(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name.split('.')[0] not in ALLOWED:
            raise ImportError('unsupported module')
        # ndarray reductions legitimately import numpy.core._methods via this hook.
        # Model AST imports remain root-only; Seatbelt still denies source/network access.
        return __import__(name, globals, locals, fromlist, level)
    safe = {name: getattr(__import__('builtins'), name) for name in
            ('abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'float', 'int', 'len', 'list',
             'max', 'min', 'print', 'range', 'reversed', 'round', 'set', 'sorted', 'str',
             'sum', 'tuple', 'zip', 'Exception', 'ValueError')}
    safe['__import__'] = importer
    namespace = {'__builtins__': safe, 'df': df, 'pd': pd, 'np': np, 'math': math, 'statistics': statistics}
    output = io.StringIO()
    failed = False
    try:
        last = None
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last = ast.Expression(tree.body.pop().value)
            ast.fix_missing_locations(last)
        with contextlib.redirect_stdout(output):
            exec(compile(tree, '<visible-rows>', 'exec'), namespace)
            if last is not None:
                result = eval(compile(last, '<visible-rows>', 'eval'), namespace)
                if result is not None:
                    print(result)
    except Exception as exc:
        output.write('\nERROR: ' + type(exc).__name__ + ': ' + str(exc)[:500])
        failed = True
    print(json.dumps({'output': (output.getvalue().strip() or 'OK')[:16000],
                      'isolation': 'seatbelt-subprocess', 'error': failed}))


if __name__ == '__main__':
    worker()
