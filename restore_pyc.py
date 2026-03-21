import os
import shutil
from pathlib import Path

# Paths
aak_dir = Path("c:/Users/ADMIN/Desktop/aak")
backup_pycache = Path("c:/Users/ADMIN/Desktop/aak_pycache_backup")
backup_modules = Path("c:/Users/ADMIN/Desktop/aak_modules_backup")

# 1. Restore root pycache items
for pyc in backup_pycache.glob("*.cpython-314.pyc"):
    base_name = pyc.name.replace(".cpython-314.pyc", ".py")
    py_file = aak_dir / base_name
    if py_file.exists() and py_file.stat().st_size == 0:
        py_file.unlink() # Delete 0 byte
    target_pyc = aak_dir / pyc.name.replace(".cpython-314.pyc", ".pyc")
    shutil.copy(pyc, target_pyc)

# 2. Restore modules pycache items
for pyc in backup_modules.rglob("*.cpython-314.pyc"):
    # Path inside modules backup
    rel_path = pyc.relative_to(backup_modules)
    
    # E.g. auth/__pycache__/routes.cpython-314.pyc
    # We want it in aak/modules/auth/routes.pyc
    parent_dir = rel_path.parent.parent # go up from __pycache__
    base_name = pyc.name.replace(".cpython-314.pyc", ".py")
    
    aak_parent = aak_dir / "modules" / parent_dir
    target_pyc = aak_parent / pyc.name.replace(".cpython-314.pyc", ".pyc")
    py_file = aak_parent / base_name
    
    if py_file.exists() and py_file.stat().st_size == 0:
        py_file.unlink()
        
    shutil.copy(pyc, target_pyc)
    
