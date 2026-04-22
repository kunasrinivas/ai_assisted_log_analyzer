from dataclasses import dataclass
from typing import List
import csv


@dataclass
class LogEvent:
    timestamp: str
    level: str
    system: str
    message: str


def read_logs(file_path: str) -> List[LogEvent]:
    """
    Reads telco OSS logs in CSV-style format and normalizes them.
    """
    events: List[LogEvent] = []

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue

            events.append(
                LogEvent(
                    timestamp=row[0],
                    level=row[1],
                    system=row[2],
                    message=row[3]
                )
            )

    return events
