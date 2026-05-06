import os
import re
import pandas as pd


# =========================
# 1. Metric Extraction Logic
# =========================

def extract_metrics_from_java(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        code = file.read()

    lines = code.splitlines()

    # Remove empty lines and comment-only lines for LOC approximation
    clean_lines = [
        line.strip()
        for line in lines
        if line.strip()
        and not line.strip().startswith("//")
        and not line.strip().startswith("*")
        and not line.strip().startswith("/*")
    ]

    loc = len(clean_lines)

    # Method detection approximation
    method_pattern = r"(public|private|protected|static|\s)+[\w\<\>\[\]]+\s+\w+\s*\([^)]*\)\s*\{"
    methods = re.findall(method_pattern, code)
    total_methods = len(methods)

    # Control flow / complexity
    if_qty = len(re.findall(r"\bif\s*\(", code))
    else_qty = len(re.findall(r"\belse\b", code))
    for_qty = len(re.findall(r"\bfor\s*\(", code))
    while_qty = len(re.findall(r"\bwhile\s*\(", code))
    switch_qty = len(re.findall(r"\bswitch\s*\(", code))
    catch_qty = len(re.findall(r"\bcatch\s*\(", code))

    loop_qty = for_qty + while_qty

    # Comparisons
    comparisons_qty = len(re.findall(r"==|!=|<=|>=|<|>", code))

    # Assignments, excluding comparison operators
    assignments_qty = len(re.findall(r"(?<![=!<>])=(?!=)", code))

    # Return statements
    return_qty = len(re.findall(r"\breturn\b", code))

    # Static invocation approximation
    nosi = len(re.findall(r"\b[A-Z][A-Za-z0-9_]*\.[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))

    # Inheritance depth approximation
    dit = 1
    if re.search(r"\bextends\b", code):
        dit = 2

    # Coupling approximation: imports + object creations
    imports = len(re.findall(r"\bimport\s+", code))
    object_creations = len(re.findall(r"\bnew\s+[A-Z][A-Za-z0-9_]*\s*\(", code))
    cbo = imports + object_creations

    # RFC approximation: method calls
    rfc = len(re.findall(r"\.\s*[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))

    # WMC approximation: methods + control flow
    wmc = total_methods + if_qty + for_qty + while_qty + switch_qty + catch_qty

    # LCOM approximation
    # Simple placeholder: higher method count with low field usage may increase cohesion issue
    fields = len(re.findall(r"(private|protected|public)\s+[\w\<\>\[\]]+\s+\w+\s*;", code))
    if total_methods > 0:
        lcom = max(0, total_methods - fields)
    else:
        lcom = 0

    # Max nested blocks approximation
    max_nested_blocks = calculate_max_nested_blocks(code)

    return {
        "file_path": file_path,
        "nosi": nosi,
        "dit": dit,
        "cbo": cbo,
        "rfc": rfc,
        "loc": loc,
        "comparisonsQty": comparisons_qty,
        "returnQty": return_qty,
        "wmc": wmc,
        "lcom": lcom,
        "totalMethods": total_methods,
        "loopQty": loop_qty,
        "assignmentsQty": assignments_qty,
        "maxNestedBlocks": max_nested_blocks
    }


def calculate_max_nested_blocks(code):
    max_depth = 0
    current_depth = 0

    for char in code:
        if char == "{":
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == "}":
            current_depth = max(0, current_depth - 1)

    return max_depth


# =========================
# 2. Scan Java Files
# =========================

def scan_java_project(project_path):
    metrics = []

    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                file_metrics = extract_metrics_from_java(file_path)
                metrics.append(file_metrics)

    return pd.DataFrame(metrics)


# =========================
# 3. Main
# =========================

if __name__ == "__main__":
    project_path = "sample_java_project"

    df = scan_java_project(project_path)

    if df.empty:
        print("No Java files found.")
    else:
        os.makedirs("data", exist_ok=True)
        output_path = "data/prediction_input_java_sample.csv"
        df.to_csv(output_path, index=False)

        print("Metric extraction completed.")
        print(f"Saved to: {output_path}")
        print(df.head())