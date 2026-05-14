import os
import re
import pandas as pd

SUPPORTED_SOURCE_EXTENSIONS = {
    ".java",
    ".py",
    ".cpp",
    ".cc",
    ".cxx",
    ".hpp",
    ".h",
    ".hh",
}


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
        "language": "Java",
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


def extract_metrics_from_python(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        code = file.read()

    lines = code.splitlines()

    clean_lines = [
        line.strip()
        for line in lines
        if line.strip()
        and not line.strip().startswith("#")
        and not line.strip().startswith('"""')
        and not line.strip().startswith("'''")
    ]

    loc = len(clean_lines)
    total_methods = len(re.findall(r"^\s*(def|async\s+def)\s+\w+\s*\(", code, re.MULTILINE))

    if_qty = len(re.findall(r"\bif\b", code))
    for_qty = len(re.findall(r"\bfor\b", code))
    while_qty = len(re.findall(r"\bwhile\b", code))
    except_qty = len(re.findall(r"\bexcept\b", code))
    match_qty = len(re.findall(r"\bmatch\b", code))
    loop_qty = for_qty + while_qty

    comparisons_qty = len(re.findall(r"==|!=|<=|>=|<|>|(?:\bis\b)|(?:\bin\b)", code))
    assignments_qty = len(re.findall(r"(?<![=!<>])=(?!=)", code))
    return_qty = len(re.findall(r"\breturn\b", code))

    imports = len(re.findall(r"^\s*(import|from)\s+", code, re.MULTILINE))
    class_names = re.findall(r"^\s*class\s+([A-Z][A-Za-z0-9_]*)", code, re.MULTILINE)
    class_name_pattern = "|".join(re.escape(name) for name in class_names)
    object_creations = 0

    if class_name_pattern:
        object_creations = len(re.findall(rf"\b({class_name_pattern})\s*\(", code))

    nosi = len(re.findall(r"\b[A-Z][A-Za-z0-9_]*\.[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))
    dit = 2 if re.search(r"^\s*class\s+\w+\s*\([^)]", code, re.MULTILINE) else 1
    cbo = imports + object_creations
    rfc = len(re.findall(r"\.\s*[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))
    wmc = total_methods + if_qty + for_qty + while_qty + except_qty + match_qty
    fields = len(re.findall(r"\bself\.[a-zA-Z_][A-Za-z0-9_]*\s*=", code))
    lcom = max(0, total_methods - fields) if total_methods > 0 else 0

    return {
        "file_path": file_path,
        "language": "Python",
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
        "maxNestedBlocks": calculate_max_indentation_depth(lines)
    }


def extract_metrics_from_cpp(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        code = file.read()

    lines = code.splitlines()

    clean_lines = [
        line.strip()
        for line in lines
        if line.strip()
        and not line.strip().startswith("//")
        and not line.strip().startswith("*")
        and not line.strip().startswith("/*")
    ]

    loc = len(clean_lines)
    total_methods = len(
        re.findall(
            r"(?:^|[;\n}])\s*(?:[\w:<>\*&]+\s+)+[A-Za-z_][A-Za-z0-9_:]*\s*\([^;{}]*\)\s*(?:const\s*)?\{",
            code,
        )
    )

    if_qty = len(re.findall(r"\bif\s*\(", code))
    for_qty = len(re.findall(r"\bfor\s*\(", code))
    while_qty = len(re.findall(r"\bwhile\s*\(", code))
    switch_qty = len(re.findall(r"\bswitch\s*\(", code))
    catch_qty = len(re.findall(r"\bcatch\s*\(", code))
    loop_qty = for_qty + while_qty

    comparisons_qty = len(re.findall(r"==|!=|<=|>=|<|>", code))
    assignments_qty = len(re.findall(r"(?<![=!<>])=(?!=)", code))
    return_qty = len(re.findall(r"\breturn\b", code))

    nosi = len(re.findall(r"\b[A-Z][A-Za-z0-9_]*::[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))
    dit = 2 if re.search(r"\bclass\s+\w+\s*:\s*(public|private|protected)\s+", code) else 1
    imports = len(re.findall(r"^\s*#\s*include\b|^\s*using\s+namespace\b", code, re.MULTILINE))
    object_creations = len(re.findall(r"\bnew\s+[A-Z][A-Za-z0-9_:]*\s*(?:\(|;)", code))
    cbo = imports + object_creations
    rfc = len(re.findall(r"(?:\.|->|::)\s*[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))
    wmc = total_methods + if_qty + for_qty + while_qty + switch_qty + catch_qty
    fields = len(re.findall(r"(private|protected|public)\s*:\s*(?:[\s\S]*?;)", code))
    lcom = max(0, total_methods - fields) if total_methods > 0 else 0

    return {
        "file_path": file_path,
        "language": "C++",
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
        "maxNestedBlocks": calculate_max_nested_blocks(code)
    }


def extract_metrics_from_source(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".java":
        return extract_metrics_from_java(file_path)

    if extension == ".py":
        return extract_metrics_from_python(file_path)

    if extension in {".cpp", ".cc", ".cxx", ".hpp", ".h", ".hh"}:
        return extract_metrics_from_cpp(file_path)

    raise ValueError(f"Unsupported source file extension: {extension}")


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


def calculate_max_indentation_depth(lines):
    max_depth = 0

    for line in lines:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        leading_spaces = len(line) - len(line.lstrip(" "))
        depth = leading_spaces // 4
        max_depth = max(max_depth, depth)

    return max_depth


# =========================
# 2. Scan Supported Source Files
# =========================

def scan_source_project(project_path):
    metrics = []

    for root, dirs, files in os.walk(project_path):
        for file in files:
            extension = os.path.splitext(file)[1].lower()

            if extension in SUPPORTED_SOURCE_EXTENSIONS:
                file_path = os.path.join(root, file)
                file_metrics = extract_metrics_from_source(file_path)
                metrics.append(file_metrics)

    return pd.DataFrame(metrics)


def scan_java_project(project_path):
    return scan_source_project(project_path)


# =========================
# 3. Main
# =========================

if __name__ == "__main__":
    project_path = "sample_java_project"

    df = scan_source_project(project_path)

    if df.empty:
        print("No supported Java, Python, or C++ files found.")
    else:
        os.makedirs("data", exist_ok=True)
        output_path = "data/prediction_input_source_sample.csv"
        df.to_csv(output_path, index=False)

        print("Metric extraction completed.")
        print(f"Saved to: {output_path}")
        print(df.head())
