from typing import Dict, List


def generate_insight(signals: List[Dict], assessment: Dict) -> str:
    """
    Generates a natural-language Service Assurance insight summary.
    """
    lines = []
    lines.append("Service Assurance Insight Summary\n")

    for signal in signals:
        lines.append(f"- Detected signal: {signal['type']} (confidence: {signal['confidence']})")

    lines.append("")
    lines.append(f"Assurance domain(s): {', '.join(assessment['assurance_domain'])}")
    lines.append(f"Service impact: {assessment['service_impact']}")
    lines.append(f"Likely root cause pattern: {assessment['root_cause_likelihood']}")
    lines.append("")
    lines.append(
        "Recommended next steps: Validate downstream dependencies, "
        "review service topology, and correlate with performance KPIs."
    )

    return "\n".join(lines)