import os
import shutil
from pathlib import Path

def refactor_to_package(repo_dir: str, package_name: str = "project"):
    base = Path(repo_dir)
    pkg = base / package_name
    
    # Files and folders to move into the new package
    to_move = [
        "app.py",
        "models.py",
        "extensions.py",
        "config.py",
        "modules",
        "templates",
        "static",
    ]
    
    if not pkg.exists():
        pkg.mkdir()
    
    # Create __init__.py for the root package
    (pkg / "__init__.py").touch()
    
    for item in to_move:
        src = base / item
        dst = pkg / item
        if src.exists() and not dst.exists():
            shutil.move(str(src), str(dst))

    # Now we need to update all python files to use absolute imports
    # from project.modules.auth import ...
    # from project.models import ...
    # from project.extensions import ...
    # from project.config import ...
    python_files = list(pkg.rglob("*.py"))
    
    for pf in python_files:
        content = pf.read_text('utf-8')
        
        # Replace local imports with absolute ones
        # Example: from models import ... -> from project.models import ...
        # Example: from extensions import ... -> from project.extensions import ...
        # Example: from config import ... -> from project.config import ...
        # Example: from modules.auth import ... -> from project.modules.auth import ...
        
        replacements = [
            ("from models import", f"from {package_name}.models import"),
            ("import models", f"import {package_name}.models"),
            ("from extensions import", f"from {package_name}.extensions import"),
            ("from config import", f"from {package_name}.config import"),
            ("from modules.", f"from {package_name}.modules."),
            ("from . ", f"from {package_name}.modules. "), # this might be risky, lets use sed later if needed map
        ]
        
        for old, new in replacements:
            content = content.replace(old, new)
            
        pf.write_text(content, 'utf-8')

if __name__ == "__main__":
    refactor_to_package(r"c:\Users\ADMIN\Desktop\aak")
