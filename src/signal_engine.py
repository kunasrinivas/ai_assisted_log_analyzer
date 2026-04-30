from collections import defaultdict
from typing import List, Dict
from log_reader import LogEvent


def extract_service_signals(events: List[LogEvent]) -> List[Dict]:
    """
    Generates service-relevant assurance signals from raw log events.
    """
    error_by_system = defaultdict(int)
    warnings = defaultdict(int)
    call_drops = 0
    network_degradation = False

    for event in events:
        if event.level == "ERROR":
            error_by_system[event.system] += 1

            if "Call dropped" in event.message:
                call_drops += 1

        if event.level == "WARN":
            warnings[event.system] += 1

            if "latency" in event.message.lower() or "packet loss" in event.message.lower():
                network_degradation = True

    signals = []

    for system, count in error_by_system.items():
        if count > 1:
            signals.append({
                "type": "ERROR_BURST",
                "system": system,
                "count": count,
                "confidence": "HIGH"
            })

    if call_drops > 0:
        signals.append({
            "type": "CALL_DROP",
            "count": call_drops,
            "confidence": "MEDIUM"
        })

    if network_degradation:
        signals.append({
            "type": "NETWORK_DEGRADATION",
            "affected_domain": "ACCESS / CORE",
            "confidence": "MEDIUM"
        })

    if not signals:
        signals.append({
            "type": "NO_ANOMALY_DETECTED",
            "confidence": "HIGH"
        })

    return signals