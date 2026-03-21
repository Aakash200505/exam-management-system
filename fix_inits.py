from pathlib import Path

modules_dir = Path("c:/Users/ADMIN/Desktop/aak/modules")
blueprints = ["auth", "dashboard", "course", "exam", "taking", "result", "analytics", "profile"]

for bp in blueprints:
    bp_dir = modules_dir / bp
    init_file = bp_dir / "__init__.py"
    
    content = f"""from flask import Blueprint\n\n{bp}_bp = Blueprint('{bp}', __name__)\n\nfrom . import routes\n"""
    
    with open(init_file, "w") as f:
        f.write(content)
        
print("Successfully generated all __init__.py files.")
