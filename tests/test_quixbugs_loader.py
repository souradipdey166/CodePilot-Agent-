from evaluation.quixbugs_loader import list_bug_names, get_bug_source, get_test_file_path

bugs = list_bug_names()
print(f"Total valid bugs found: {len(bugs)}")
print("First 10:", bugs[:10])

# Confirm bucketsort is in there
assert "bucketsort" in bugs
print("\nbucketsort.py source:")
print(get_bug_source("bucketsort"))

print("\nTest file path:", get_test_file_path("bucketsort"))