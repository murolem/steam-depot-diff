import sys
import os

# Source - https://stackoverflow.com/a/53605128
# Posted by Kamal, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-11, License - CC BY-SA 4.0

# path pointing to project root that changes based on whether the program is run in development vs in binary.
# files that get included in the binary must be referred to using this path as a base.
# the path includes a trailing separator so it can be simply concatenated to any path.
inner_binary_path: str
if getattr(sys, 'frozen', False):
    inner_binary_path = sys._MEIPASS + os.path.sep
else:
    inner_binary_path = "./"