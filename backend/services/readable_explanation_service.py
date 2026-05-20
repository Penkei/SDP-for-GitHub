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
        signals = []

        if "method interaction complexity" in explanation_lower:
            signals.append("method interaction complexity")

        if "number of conditional checks" in explanation_lower:
            signals.append("conditional checks")

        if "static method usage" in explanation_lower:
            signals.append("static method usage")

        if "class cohesion complexity" in explanation_lower:
            signals.append("class cohesion complexity")

        if "number of methods" in explanation_lower:
            signals.append("number of methods")

        if "file size" in explanation_lower:
            signals.append("file size")

        if "dependency between classes" in explanation_lower:
            signals.append("class dependency level")

        if "overall method complexity" in explanation_lower:
            signals.append("method complexity")

        if "number of return paths" in explanation_lower:
            signals.append("return paths")

        if "inheritance depth" in explanation_lower:
            signals.append("inheritance depth")

        if "historical file change frequency" in explanation_lower:
            signals.append("file change history")

        if "previous bug-fix activity" in explanation_lower:
            signals.append("previous bug-fix history")

        if "recent file change activity" in explanation_lower:
            signals.append("recent file changes")

        if "time since the file was last changed" in explanation_lower:
            signals.append("time since last change")

        if "lines added in the previous file change" in explanation_lower:
            signals.append("lines added in the previous change")

        if "lines deleted in the previous file change" in explanation_lower:
            signals.append("lines deleted in the previous change")

        if "code churn in the previous file change" in explanation_lower:
            signals.append("previous change churn")

        if "files changed together in the previous commit" in explanation_lower:
            signals.append("files changed together")

        if "selected commit author's prior changes" in explanation_lower:
            signals.append("author's previous changes to this file")

        if not signals:
            signals.append("several metric patterns")

        return signals

    def _high_risk_explanation(self, probability_percent: float, reason_text: str) -> str:
        return (
            f"The model gives this file a high defect risk score ({probability_percent}%). "
            f"The strongest signals are {reason_text}. "
            "This does not prove the file contains a bug, but it means the file looks similar "
            "to higher-risk examples seen during training. Review it before lower-risk files."
        )

    def _medium_risk_explanation(self, probability_percent: float, reason_text: str) -> str:
        return (
            f"The model gives this file a medium defect risk score ({probability_percent}%). "
            f"The main signals are {reason_text}. "
            "The result is not an urgent warning, but these areas are worth checking if the file "
            "is part of the current change."
        )

    def _low_risk_explanation(self, probability_percent: float, reason_text: str) -> str:
        return (
            f"The model gives this file a low defect risk score ({probability_percent}%). "
            f"It still considered signals such as {reason_text}, "
            "but they did not strongly push the prediction toward higher risk. "
            "Review is optional unless this file is important to the current change."
        )

    def _format_reason_text(self, reasons: list) -> str:
        if len(reasons) == 1:
            return reasons[0]

        if len(reasons) == 2:
            return f"{reasons[0]} and {reasons[1]}"

        return ", ".join(reasons[:-1]) + f", and {reasons[-1]}"
