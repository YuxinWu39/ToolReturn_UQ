"""Execute generated pandas code in a credential-free macOS Seatbelt process."""
import ctypes
import resource
import json
from pathlib import Path
import subprocess
import sys


def execute(task, bench_dir, code):
    worker = Path(__file__).resolve()
    child = subprocess.run(
        [sys.executable, "-I", "-B", str(worker)], check=True, timeout=30,
        input=json.dumps([task, str(bench_dir.resolve()), code]), text=True, capture_output=True,
        env={"PATH": "/usr/bin:/bin", "OPENBLAS_NUM_THREADS": "1", "TZ": "UTC"},
    )
    return json.loads(child.stdout)


def restrict_process():
    # Install the policy after trusted imports and table loading, before evaluating
    # model code. Pandas may still need to import modules from the Python environment.
    roots = {sys.prefix, sys.base_prefix, "/System/Library", "/usr/lib"}
    reads = " ".join(f"(subpath {json.dumps(p)})" for p in sorted(roots))
    policy = f"(version 1)(deny default)(allow sysctl-read)(allow file-read* {reads})"
    lib = ctypes.CDLL("/usr/lib/libsandbox.dylib")
    lib.sandbox_init.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_char_p)]
    error = ctypes.c_char_p()
    if lib.sandbox_init(policy.encode(), 0, ctypes.byref(error)):
        raise RuntimeError(f"Could not isolate python_exec: {error.value!r}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from p4_run import TieredEnv
    task, directory, code = json.load(sys.stdin)
    env = TieredEnv(task, Path(directory), toxic=False)
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    restrict_process()
    value = env.python_exec(code)
    print(json.dumps([value, env._last_exec_norm]))
