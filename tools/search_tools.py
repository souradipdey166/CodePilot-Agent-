from pathlib import Path

def search_text(directory: str, query: str, extension: str = ".py") -> list[dict]:
    """Search for a text string across files, return matches with file + line number."""
    matches = []
    for file in Path(directory).glob(f"*{extension}"):
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if query.lower() in line.lower():
                matches.append({"file": file.name, "line": i, "text": line.strip()})
    return matches