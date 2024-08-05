#!/usr/bin/env python
import os
import re
import sys
from src.renee.__main__ import main

# add script directory to the path to allow the CLI to work out-of-the-box
# without the need to install it via pip first
SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "renee")
sys.path.append(SCRIPT_DIR)

if (
    __name__ == "__main__"
):  # this block is adapted from the executable file created by `pip install`
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
