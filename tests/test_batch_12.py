from evaluation.run_evaluation import run_batch

bugs = ["bucketsort", "bitcount", "mergesort", "levenshtein", "gcd", "flatten",
        "sqrt", "to_base", "next_permutation", "kth", "powerset", "max_sublist_sum"]

error_reports = {"levenshtein": 'AssertionError: levenshtein("electron", "neutron") returned 8, expected 3'}

run_batch(bugs, error_reports)