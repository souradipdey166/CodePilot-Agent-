from pathlib import Path
'''
def list_files(directory: str, extension: str = ".py") -> list[str]:
    """List all files of a given type in a directory."""
    files = list(Path(directory).glob(f"*{extension}"))
    return [f.name for f in files]
'''
from pathlib import Path

def list_files(directory: str, extension: str = ".py") -> list[str]:
    files = list(Path(directory).rglob(f"*{extension}"))
    return [str(f) for f in files]

def read_file(directory: str, filename: str) -> str:
    """Read the full contents of a specific file."""
    full_path = Path(directory) / filename
    return full_path.read_text(encoding="utf-8", errors="ignore")