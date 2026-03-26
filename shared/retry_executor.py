"""
Retry executor — subprocess and function-call retry wrappers.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Used by agent dispatchers (run.py) for resilient execution.
"""

import subprocess
import sys
import time
from typing import Any, Callable


def retry_subprocess(
    cmd: list[str],
    *,
    max_retries: int = 2,
    task_label: str = "",
    timeout: int = 300,
) -> subprocess.CompletedProcess:
    """Run a subprocess with retry logic on non-zero exit codes.

    Args:
        cmd:         Command list (e.g. [sys.executable, "script.py", ...]).
        max_retries: Number of retry attempts after first failure.
        task_label:  Label for log messages.
        timeout:     Per-attempt timeout in seconds.

    Returns a CompletedProcess (may have non-zero returncode on final failure).
    """
    label = task_label or " ".join(cmd[:3])
    last_result = None

    for attempt in range(max_retries + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                timeout=timeout,
            )
            if result.returncode == 0:
                return result
            last_result = result
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  [retry] {label} failed (exit {result.returncode}), "
                      f"retrying in {wait}s ({attempt + 1}/{max_retries})")
                time.sleep(wait)
        except subprocess.TimeoutExpired:
            print(f"  [retry] {label} timed out after {timeout}s "
                  f"(attempt {attempt + 1}/{max_retries + 1})")
            last_result = subprocess.CompletedProcess(cmd, returncode=-1)
            if attempt < max_retries:
                time.sleep(2 ** attempt)

    return last_result or subprocess.CompletedProcess(cmd, returncode=-1)


def retry_call(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = 2,
    task_label: str = "",
    **kwargs: Any,
) -> Any:
    """Call a function with retry logic on exceptions.

    Args:
        fn:          The callable to invoke.
        max_retries: Number of retry attempts after first failure.
        task_label:  Label for log messages.
        *args, **kwargs: Passed through to fn.

    Returns whatever fn returns on success.
    Raises the last exception if all attempts fail.
    """
    label = task_label or getattr(fn, "__name__", "call")
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** attempt
                print(f"  [retry] {label} raised {type(e).__name__}, "
                      f"retrying in {wait}s ({attempt + 1}/{max_retries})")
                time.sleep(wait)

    raise last_error  # type: ignore[misc]
