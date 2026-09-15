from tools.patch_tools import apply_patch

# Test on a COPY first, not the real file, to avoid corrupting your only buggy copy
import shutil
shutil.copy("quixbugs_data/python_programs/bucketsort.py", "quixbugs_data/python_programs/bucketsort_test_copy.py")

success = apply_patch(
    "quixbugs_data/python_programs",
    "bucketsort_test_copy.py",
    "for i, count in enumerate(arr):",
    "for i, count in enumerate(counts):"
)
print("Patch applied:", success)

from tools.file_tools import read_file
print(read_file("quixbugs_data/python_programs", "bucketsort_test_copy.py"))