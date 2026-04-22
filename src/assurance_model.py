from typing import List, Dict


def classify_assurance(signals: List[Dict]) -> Dict:
    """
    Maps technical signals to Service Assurance interpretation.
    """
    assessment = {
        "assurance_domain": set(),
        "service_impact": "UNKNOWN",
        "root_cause_likelihood": "UNDETERMINED"
    }

    for signal in signals:
        if signal["type"] in {"NETWORK_DEGRADATION", "ERROR_BURST"}:
            assessment["assurance_domain"].add("PERFORMANCE")

        if signal["type"] == "CALL_DROP":
            assessment["assurance_domain"].add("SERVICE QUALITY")
            assessment["service_impact"] = "CUSTOMER-FACING"

    if "PERFORMANCE" in assessment["assurance_domain"]:
        assessment["root_cause_likelihood"] = "POSSIBLE_DEPENDENCY_OR_CAPACITY"

    assessment["assurance_domain"] = list(assessment["assurance_domain"])
    return assessment