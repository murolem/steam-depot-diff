#!/usr/bin/env python3

import os.path
import subprocess

dd_diff_help_command = "./main.py --help"
readme_template_file = "README-template.md"
readme_file = "README.md"
help_marker = '%PROGRAM_HELP_OUTPUT'

if not os.path.exists(readme_template_file):
    raise Exception("readme template file not found: " + readme_template_file)

help_output = subprocess.check_output(dd_diff_help_command.split()).decode("utf-8")

with open(readme_template_file, 'r+') as f:
    contents = f.read().replace(help_marker, help_output)

with open(readme_file, "w") as f:
    f.write(contents)