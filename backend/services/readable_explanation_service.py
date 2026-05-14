class ReadableExplanationService:

    def generate(self, explanation: str, risk_level: str, probability: float) -> str:
        explanation_lower = explanation.lower()

        reasons = self._extract_reasons(explanation_lower)
        reason_text = self._format_reason_text(reasons)
        probability_percent = round(probability * 100, 2)

        if risk_level == "High":
            return self._high_risk_explanation(probability_percent, reason_text)

        if risk_level == "Medium":
            return self._medium_risk_explanation(probability_percent, reason_text)

        return self._low_risk_explanation(probability_percent, reason_text)

    def _extract_reasons(self, explanation_lower: str) -> list:
        reasons = []

        if "method interaction complexity" in explanation_lower:
            reasons.append("many method interactions")

        if "number of conditional checks" in explanation_lower:
            reasons.append("many if/else or comparison checks")

        if "static method usage" in explanation_lower:
            reasons.append("frequent static method usage")

        if "class cohesion complexity" in explanation_lower:
            reasons.append("weaker class cohesion")

        if "number of methods" in explanation_lower:
            reasons.append("many methods in one file")

        if "file size" in explanation_lower:
            reasons.append("large file size")

        if "dependency between classes" in explanation_lower:
            reasons.append("many dependencies between classes")

        if "overall method complexity" in explanation_lower:
            reasons.append("complex method logic")

        if "number of return paths" in explanation_lower:
            reasons.append("many return paths")

        if "inheritance depth" in explanation_lower:
            reasons.append("deeper inheritance structure")

        if not reasons:
            reasons.append("several code metric patterns")

        return reasons

    def _high_risk_explanation(self, probability_percent: float, reason_text: str) -> str:
        return (
            f"This file has a high defect risk ({probability_percent}%). "
            f"The main reasons are {reason_text}. "
            "These patterns suggest the file may be complex, harder to test, "
            "and more likely to introduce defects if changed. It should be reviewed first."
        )

    def _medium_risk_explanation(self, probability_percent: float, reason_text: str) -> str:
        return (
            f"This file has a medium defect risk ({probability_percent}%). "
            f"The model noticed {reason_text}. "
            "The file is not marked as highly risky, but the highlighted areas should be checked "
            "if this file is part of an active change."
        )

    def _low_risk_explanation(self, probability_percent: float, reason_text: str) -> str:
        return (
            f"This file has a low defect risk ({probability_percent}%). "
            f"Some patterns were still detected, such as {reason_text}, "
            "but they are not strong enough for the model to classify the file as high risk. "
            "No urgent review is needed unless this file is being modified."
        )

    def _format_reason_text(self, reasons: list) -> str:
        if len(reasons) == 1:
            return reasons[0]

        if len(reasons) == 2:
            return f"{reasons[0]} and {reasons[1]}"

        return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"