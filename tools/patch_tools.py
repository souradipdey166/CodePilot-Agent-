from pathlib import Path

def apply_patch(directory: str, filename: str, old_code: str, new_code: str) -> bool:
    """Replace old_code with new_code in the target file. Returns True if the replacement was made."""
    full_path = Path(directory) / filename
    content = full_path.read_text(encoding="utf-8")
    
    if old_code not in content:
        return False
    
    new_content = content.replace(old_code, new_code, 1)
    full_path.write_text(new_content, encoding="utf-8")
    return True