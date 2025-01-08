# meter_changes.py
from dataclasses import dataclass
from datetime import datetime
import yaml
from typing import Dict, List

@dataclass
class MeterChange:
	date: datetime
	column: str  # strom/gas/etc
	offset: int
	reason: str = ""

def load_meter_changes(file_path: str = 'meter_changes.yaml') -> Dict[str, List[MeterChange]]:
	with open(file_path, 'r') as f:
		data = yaml.safe_load(f)
		
	changes = {}
	for col, entries in data.items():
		changes[col] = [
			MeterChange(
				date=datetime.strptime(entry['date'], '%Y-%m-%d'),
				column=col,
				offset=entry['offset'],
				reason=entry.get('reason', '')
			) for entry in entries
		]
	return changes