#!/usr/bin/env python3
import os
import importlib
from src.build import app

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(current_dir, "src")

# Loop through all Python files
non_imports = ["build.py", "app.py"]

for filename in os.listdir(target_dir):
    if filename.endswith(".py") and filename not in non_imports:
        module_name = "src." + filename[:-3]  # Strip '.py' extension
        importlib.import_module(module_name)

app.synth()
