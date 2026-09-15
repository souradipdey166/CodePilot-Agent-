import sys
sys.path.insert(0, "quixbugs_data/python_programs")
from levenshtein import levenshtein

try:
    result = levenshtein("electron", "neutron")
    print("Result:", result, "(expected: 3)")
except Exception as e:
    import traceback
    traceback.print_exc()