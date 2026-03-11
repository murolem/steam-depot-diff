#!/usr/bin/env python3
import os
import sys
import platform

version_filename = "VERSION"

if not os.path.exists(version_filename):
    raise Exception("Version file not found at: " + version_filename)

with open(version_filename, "r") as f:
    version = f.read().strip()

if __name__ == "__main__":
    print(f"depot-diff-{sys.platform}-{platform.machine()}-{version}")
