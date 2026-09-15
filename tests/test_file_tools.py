from tools.file_tools import list_files, read_file
from tools.search_tools import search_text

QUIXBUGS_PROGRAMS = "quixbugs_data/python_programs"

files = list_files(QUIXBUGS_PROGRAMS)
print(f"Found {len(files)} Python files")
print("Sample:", files[:5])

content = read_file(QUIXBUGS_PROGRAMS, "bucketsort.py")
print("\nbucketsort.py content:")
print(content[:200])

results = search_text(QUIXBUGS_PROGRAMS, "enumerate")
print(f"\nFound {len(results)} matches for 'enumerate'")
for r in results[:3]:
    print(f"  {r['file']}:{r['line']} -> {r['text']}")