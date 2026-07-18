#!/usr/bin/env python3
"""Python CLI entry point for VEILos."""

import os
import sys

from veil_core import execute_command, get_kernel


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    stealth_mode = any(arg == "--stealth" for arg in argv)
    if stealth_mode:
        os.environ["VEIL_STEALTH"] = "1"
    else:
        os.environ.pop("VEIL_STEALTH", None)
    kernel = get_kernel()
    if stealth_mode:
        kernel.set_stealth_mode(True)

    print("VEILos CLI")
    print("[Stealth Mode Active]" if stealth_mode else "[Development Mode]")
    print("Type 'help' for available commands or 'exit' to quit.")

    while True:
        prompt = "> " if stealth_mode else "veilos> "
        try:
            command = input(prompt).strip()
        except EOFError:
            print()
            break

        if not command:
            continue
        if command == "exit":
            break

        print(execute_command(command))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
