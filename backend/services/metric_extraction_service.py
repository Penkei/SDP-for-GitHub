import os
import re
import pandas as pd


class MetricExtractionService:
<<<<<<< HEAD
=======
    MAX_FULL_REPOSITORY_FILES = 300

>>>>>>> Refinement
    LANGUAGE_BY_EXTENSION = {
        ".java": "Java",
        ".py": "Python",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".hpp": "C++",
        ".h": "C++",
        ".hh": "C++",
    }

<<<<<<< HEAD
    def extract_from_project(self, project_path: str) -> pd.DataFrame:
        metrics = []

        for root, dirs, files in os.walk(project_path):
            for file in files:
=======
    EXCLUDE_PATH_KEYWORDS = [
        "/.git/",
        "/test/",
        "/tests/",
        "/target/",
        "/build/",
        "/generated/",
        "/vendor/",
        "/third_party/",
        "/node_modules/",
        "/dist/",
    ]

    def extract_from_project(
        self,
        project_path: str,
        target_files: list[str] = None
    ) -> pd.DataFrame:
        if target_files is not None:
            return self.extract_from_target_files(project_path, target_files)

        metrics = []

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [
                directory for directory in dirs
                if not self.should_exclude_path(directory)
            ]

            for file in files:
                if len(metrics) >= self.MAX_FULL_REPOSITORY_FILES:
                    return pd.DataFrame(metrics)

>>>>>>> Refinement
                extension = os.path.splitext(file)[1].lower()

                if extension not in self.LANGUAGE_BY_EXTENSION:
                    continue

                file_path = os.path.join(root, file)
<<<<<<< HEAD
                file_metrics = self.extract_from_file(file_path, extension)

                relative_path = os.path.relpath(file_path, project_path)
=======
                relative_path = os.path.relpath(file_path, project_path)

                if not self.is_supported_source_path(relative_path):
                    continue

                file_metrics = self.extract_from_file(file_path, extension)
>>>>>>> Refinement
                file_metrics["file_path"] = relative_path
                file_metrics["language"] = self.LANGUAGE_BY_EXTENSION[extension]

                metrics.append(file_metrics)

        return pd.DataFrame(metrics)

<<<<<<< HEAD
=======
    def extract_from_target_files(self, project_path: str, target_files: list[str]) -> pd.DataFrame:
        metrics = []

        for relative_path in target_files:
            if not self.is_supported_source_path(relative_path):
                continue

            safe_relative_path = relative_path.replace("/", os.sep)
            file_path = os.path.normpath(os.path.join(project_path, safe_relative_path))
            project_root = os.path.abspath(project_path)

            if not os.path.abspath(file_path).startswith(project_root):
                continue

            if not os.path.exists(file_path):
                continue

            extension = os.path.splitext(file_path)[1].lower()
            file_metrics = self.extract_from_file(file_path, extension)
            file_metrics["file_path"] = relative_path
            file_metrics["language"] = self.LANGUAGE_BY_EXTENSION[extension]
            metrics.append(file_metrics)

        return pd.DataFrame(metrics)

    def is_supported_source_path(self, file_path: str) -> bool:
        normalized_path = self._normalize_path(file_path)
        extension = os.path.splitext(normalized_path)[1]

        if extension not in self.LANGUAGE_BY_EXTENSION:
            return False

        return not self.should_exclude_path(normalized_path)

    def should_exclude_path(self, path: str) -> bool:
        normalized_path = self._normalize_path(path)

        return any(keyword in normalized_path for keyword in self.EXCLUDE_PATH_KEYWORDS)

    def _normalize_path(self, path: str) -> str:
        return f"/{str(path).replace(os.sep, '/').lower().strip('/')}"

>>>>>>> Refinement
    def extract_from_file(self, file_path: str, extension: str) -> dict:
        if extension == ".java":
            return self.extract_from_java_file(file_path)

        if extension == ".py":
            return self.extract_from_python_file(file_path)

        return self.extract_from_cpp_file(file_path)

    def extract_from_java_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            code = file.read()

        return self._extract_brace_language_metrics(
            code=code,
            comment_prefixes=("//", "*", "/*"),
            method_pattern=r"(public|private|protected|static|\s)+[\w\<\>\[\]]+\s+\w+\s*\([^)]*\)\s*\{",
            import_pattern=r"\bimport\s+",
            object_creation_pattern=r"\bnew\s+[A-Z][A-Za-z0-9_]*\s*\(",
            inheritance_pattern=r"\bextends\b",
            field_pattern=r"(private|protected|public)\s+[\w\<\>\[\]]+\s+\w+\s*;",
            static_call_pattern=r"\b[A-Z][A-Za-z0-9_]*\.[a-zA-Z_][A-Za-z0-9_]*\s*\(",
        )

    def extract_from_python_file(self, file_path: str) -> dict:
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

        comparisons_qty = len(re.findall(r"==|!=|<=|>=|<|>|(?:\bis\b)|(?:\bin\b)", code))
        return_qty = len(re.findall(r"\breturn\b", code))
        imports = len(re.findall(r"^\s*(import|from)\s+", code, re.MULTILINE))

        class_names = re.findall(r"^\s*class\s+([A-Z][A-Za-z0-9_]*)", code, re.MULTILINE)
        class_name_pattern = "|".join(re.escape(name) for name in class_names)
        object_creations = 0

        if class_name_pattern:
            object_creations = len(re.findall(rf"\b({class_name_pattern})\s*\(", code))

        cbo = imports + object_creations
        rfc = len(re.findall(r"\.\s*[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))
        nosi = len(re.findall(r"\b[A-Z][A-Za-z0-9_]*\.[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))
        dit = 2 if re.search(r"^\s*class\s+\w+\s*\([^)]", code, re.MULTILINE) else 1
        wmc = total_methods + if_qty + for_qty + while_qty + except_qty + match_qty

        fields = len(re.findall(r"\bself\.[a-zA-Z_][A-Za-z0-9_]*\s*=", code))
        lcom = max(0, total_methods - fields) if total_methods > 0 else 0

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

    def extract_from_cpp_file(self, file_path: str) -> dict:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            code = file.read()

        return self._extract_brace_language_metrics(
            code=code,
            comment_prefixes=("//", "*", "/*"),
            method_pattern=r"(?:^|[;\n}])\s*(?:[\w:<>\*&]+\s+)+[A-Za-z_][A-Za-z0-9_:]*\s*\([^;{}]*\)\s*(?:const\s*)?\{",
            import_pattern=r"^\s*#\s*include\b|^\s*using\s+namespace\b",
            object_creation_pattern=r"\bnew\s+[A-Z][A-Za-z0-9_:]*\s*(?:\(|;)",
            inheritance_pattern=r"\bclass\s+\w+\s*:\s*(public|private|protected)\s+",
            field_pattern=r"(private|protected|public)\s*:\s*(?:[\s\S]*?;)",
            static_call_pattern=r"\b[A-Z][A-Za-z0-9_]*::[a-zA-Z_][A-Za-z0-9_]*\s*\(",
        )

    def _extract_brace_language_metrics(
        self,
        code: str,
        comment_prefixes: tuple,
        method_pattern: str,
        import_pattern: str,
        object_creation_pattern: str,
        inheritance_pattern: str,
        field_pattern: str,
        static_call_pattern: str,
    ) -> dict:
        lines = code.splitlines()

        clean_lines = [
            line.strip()
            for line in lines
            if line.strip()
            and not line.strip().startswith(comment_prefixes)
        ]

        loc = len(clean_lines)

        methods = re.findall(method_pattern, code)
        total_methods = len(methods)

        if_qty = len(re.findall(r"\bif\s*\(", code))
        for_qty = len(re.findall(r"\bfor\s*\(", code))
        while_qty = len(re.findall(r"\bwhile\s*\(", code))
        switch_qty = len(re.findall(r"\bswitch\s*\(", code))
        catch_qty = len(re.findall(r"\bcatch\s*\(", code))

        comparisons_qty = len(re.findall(r"==|!=|<=|>=|<|>", code))
        return_qty = len(re.findall(r"\breturn\b", code))

        nosi = len(re.findall(static_call_pattern, code))

        dit = 2 if re.search(inheritance_pattern, code) else 1

        imports = len(re.findall(import_pattern, code, re.MULTILINE))
        object_creations = len(re.findall(object_creation_pattern, code))
        cbo = imports + object_creations

        rfc = len(re.findall(r"(?:\.|->|::)\s*[a-zA-Z_][A-Za-z0-9_]*\s*\(", code))

        wmc = total_methods + if_qty + for_qty + while_qty + switch_qty + catch_qty

        fields = len(re.findall(field_pattern, code))

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
