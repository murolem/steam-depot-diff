#!/usr/bin/env python3

import sys
import platform

if __name__ == "__main__":
    print(f"depot-diff-{sys.platform}-{platform.machine()}")
