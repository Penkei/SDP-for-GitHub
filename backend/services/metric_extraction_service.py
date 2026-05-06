import os
import re
import pandas as pd


class MetricExtractionService:

    def extract_from_project(self, project_path: str) -> pd.DataFrame:
        metrics = []

        for root, dirs, files in os.walk(project_path):
            for file in files:
                if file.endswith(".java"):
                    file_path = os.path.join(root, file)
                    file_metrics = self.extract_from_java_file(file_path)

                    relative_path = os.path.relpath(file_path, project_path)
                    file_metrics["file_path"] = relative_path

                    metrics.append(file_metrics)

        return pd.DataFrame(metrics)

    def extract_from_java_file(self, file_path: str) -> dict:
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

        method_pattern = r"(public|private|protected|static|\s)+[\w\<\>\[\]]+\s+\w+\s*\([^)]*\)\s*\{"
        methods = re.findall(method_pattern, code)
        total_methods = len(methods)

        if_qty = len(re.findall(r"\bif\s*\(", code))
        for_qty = len(re.findall(r"\bfor\s*\(", code))
        while_qty = len(re.findall(r"\bwhile\s*\(", code))
        switch_qty = len(re.findall(r"\bswitch\s*\(", code))
        catch_qty = len(re.findall(r"\bcatch\s*\(", code))

        comparisons_qty = len(re.findall(r"==|!=|<=|>=|<|>", code))
        return_qty = len(re.findall(r"\breturn\b", code))

        nosi = len(
            re.findall(
                r"\b[A-Z][A-Za-z0-9_]*\.[a-zA-Z_][A-Za-z0-9_]*\s*\(",
                code
            )
        )

        dit = 2 if re.search(r"\bextends\b", code) else 1

        imports = len(re.findall(r"\bimport\s+", code))
        object_creations = len(re.findall(r"\bnew\s+[A-Z][A-Za-z0-9_]*\s*\(", code))
        cbo = imports + object_creations

        rfc = len(re.findall(r"\.\s*[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))

        wmc = total_methods + if_qty + for_qty + while_qty + switch_qty + catch_qty

        fields = len(
            re.findall(
                r"(private|protected|public)\s+[\w\<\>\[\]]+\s+\w+\s*;",
                code
            )
        )

        if total_methods > 0:
            lcom = max(0, total_methods - fields)
        else:
            lcom = 0

        return {
            "nosi": nosi,
            "dit": dit,
            "cbo": cbo,
            "rfc": rfc,
            "loc": loc,
            "comparisonsQty": comparisons_qty,
            "returnQty": return_qty,
            "wmc": wmc,
            "lcom": lcom,
            "totalMethods": total_methods
        }