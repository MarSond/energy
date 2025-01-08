# energy_util.py
import pandas as pd
from datetime import datetime
import numpy as np
import os
from constants import *
from dataclasses import dataclass
from datetime import datetime
import yaml
from typing import Dict, List

csv_data_columns = [STROM, WASSER, GAS, DLE, EINSPEISUNG, GARTEN] 

df_renames_display = {
	DLE: 'DLE',
	EINSPEISUNG: 'Einspeisung',
	GAS: 'Gas',
	STROM: 'Strom',
	WASSER: 'Wasser',
	GARTEN: 'Garten',
	DATUM: 'Datum'
}

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
	if data is None or len(data) == 0:
		return changes
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

def format_date_for_display(date_input):
    """ Convert date from various formats to DD.MM.YYYY format for display purposes. """
    try:
        if isinstance(date_input, str):
            date_obj = pd.to_datetime(date_input)
        else:
            date_obj = pd.Timestamp(date_input)
        return date_obj.strftime(DATE_STR_DOT)
    except Exception:
        raise ValueError("Ungültiges Datumsformat. Bitte verwenden Sie ein gültiges Datum.")

def format_date_for_storage(date_str):
    """ Convert date from various formats to YYYY-MM-DD format for storage purposes. """
    try:
        date_obj = pd.to_datetime(date_str)
        return date_obj.strftime(DATE_STR_DASH)
    except Exception as e:
        raise ValueError(f"Ungültiges Datumsformat. Fehler: {str(e)}")

def save_data(df: pd.DataFrame, sep=';', decimal=','):
    csv_file_path = get_data_file_path()
    """ Save data to a CSV file, using the specified delimiter and decimal format. """
    df.to_csv(csv_file_path, index=True, sep=sep, decimal=decimal, date_format=DATE_STR_DASH)

def get_data_file_path():
    """ Return the path to the CSV data file. """
    # data csv if on windows, /var/www/data.csv if on linux
    if os.name == 'nt':
        return DEV_FILENAME # dev environment
    else:
        return PROD_FILENAME # production environment

def apply_meter_changes(df: pd.DataFrame) -> pd.DataFrame:
	"""Wendet die dokumentierten Zählerkorrekturen an."""
	df_corrected = df.copy()
	changes = load_meter_changes()
	
	for column, meter_changes in changes.items():
		if column not in df.columns:
			continue
			
		for change in sorted(meter_changes, key=lambda x: x.date):
			# Addiere Offset zu allen Werten nach dem Änderungsdatum
			mask = df_corrected.index >= change.date
			df_corrected.loc[mask, column] += change.offset
	
	return df_corrected


def get_data():
    """ Retrieve and format data from a CSV file. """
    csv_file_path = get_data_file_path()
    df = pd.read_csv(csv_file_path, delimiter=';', decimal=',', parse_dates=[DATUM])
    df[DATUM] = pd.to_datetime(df[DATUM]).dt.normalize()  # Normalize to remove time part
    df.set_index('datum', inplace=True)
    df[csv_data_columns] = df[csv_data_columns].apply(pd.to_numeric, errors='coerce')
    df[csv_data_columns] = df[csv_data_columns].apply(np.floor).astype('Int64')
    df = apply_meter_changes(df)
    return df

def prepare_data_for_list_display():
    """ Prepare data for display in a list format. """
    df = get_data()
    df_reset = df.reset_index()  # Reset index to manipulate 'datum' as a column
    # Apply date formatting
    df_reset[DATUM] = df_reset[DATUM].apply(format_date_for_display)
    # Rename columns according to display names
    df_reset.rename(columns=df_renames_display, inplace=True)
    
    # Reorder DataFrame from newest to oldest
    df_reset = df_reset.iloc[::-1]

    # Return as dictionary for display purposes
    return df_reset.to_dict(orient='records')


def calculate_averages(df, freq):
	""" Calculate mean values for given frequency (D, W, M, Y) """
	return df.resample(freq).mean()


def get_data_for_type(type):
    # Here, implement fetching data logic based on 'type'
    # Example placeholder logic
    df = get_data()  # Assuming util.get_data() fetches a DataFrame with all data
    if type in df.columns:
        return df[[type]].dropna().to_dict(orient='index')
    return {}

def prepare_all_data():
    # Assuming you have a way to access data for each type
    types = [STROM, WASSER, GAS, DLE, EINSPEISUNG, GARTEN]
    all_data = {}
    for type in types:
        all_data[type] = get_data_for_type(type)  # You need to implement this function
    return all_data


def prepare_data_for_graphs(resource_type, timeframe):
	df = get_data(get_data_file_path())
	df = df[[resource_type]].interpolate()  # focusing on one resource type and interpolate missing

	# Aggregate data based on the requested timeframe
	if timeframe == 'D':
		data = df.resample('D').sum()  # Daily sums
	elif timeframe == 'W':
		data = df.resample('W').mean()  # Weekly averages
	elif timeframe == 'M':
		data = df.resample('M').mean()  # Monthly averages
	elif timeframe == 'Y':
		data = df.resample('A').mean()  # Annual averages
	else:
		data = df

	# Prepare data for year-over-year analysis if needed
	if timeframe in ['M', 'Y']:
		data[YEAR] = data.index.year
		data[MONTH] = data.index.month
		yearly_data = data.pivot_table(index=MONTH, columns=YEAR, values=resource_type)

		return data, yearly_data.to_dict()

	return data

# Ergänzungen in energy_util.py

def get_strom_data():
    df = get_data()
    df[DATUM] = pd.to_datetime(df.index).normalize()  # Datum normalisieren, um die Uhrzeit zu entfernen
    
    # Interpolieren der Daten
    # Es soll auf Tages ebene genau sein!
    df[STROM] = df[STROM].interpolate()
    
    # Akkumulierter Verlauf
    accumulated = df[STROM].cumsum().reset_index()
    accumulated[DATUM] = accumulated[DATUM].dt.strftime(DATE_STR_DASH)  # Datum formatieren
    
    # Verbrauch in diesem Jahr (Differenz)
    df_current_year = df[df[DATUM].dt.year == datetime.now().year]
    consumption_diff = df_current_year[STROM].diff().dropna().reset_index()
    consumption_diff[DATUM] = consumption_diff[DATUM].dt.strftime(DATE_STR_DASH)  # Datum formatieren
    
    # Durchschnitt über alle Jahre interpoliert
    df[MONTH] = df[DATUM].dt.month
    monthly_avg = df.groupby(MONTH)[STROM].mean().reset_index()
    monthly_avg[CURRENT_YEAR] = df_current_year.groupby(df_current_year[DATUM].dt.month)[STROM].sum().reset_index()[STROM]
    
    return accumulated, consumption_diff, monthly_avg

def analyze_metric(df: pd.DataFrame, metric_name: str) -> dict:
	"""Analysiert eine Metrik und gibt relevante Statistiken zurück."""
	if metric_name not in df.columns:
		raise ValueError(f"Metrik {metric_name} nicht in DataFrame gefunden")
	
	data = df[metric_name].dropna()
	
	# Basis-Statistiken
	stats = {
		"min": float(data.min()),
		"max": float(data.max()),
		"mean": float(data.mean()),
		"median": float(data.median()),
		"current": float(data.iloc[-1]),
	}
	
	# Trend der letzten 30 Tage
	last_30_days = data[-30:]
	trend = float(last_30_days.iloc[-1] - last_30_days.iloc[0])
	
	# Saisonale Analyse
	monthly_avg = data.groupby(data.index.month).mean()
	peak_month = int(monthly_avg.idxmax())
	low_month = int(monthly_avg.idxmin())
	
	# Anomalien (Werte außerhalb von 2 Standardabweichungen)
	std = data.std()
	mean = data.mean()
	anomalies = data[abs(data - mean) > 2 * std]
	
	return {
		"basic_stats": stats,
		"trend": {
			"value": trend,
			"is_increasing": trend > 0
		},
		"seasonal": {
			"monthly_avg": monthly_avg.to_dict(),
			"peak_month": peak_month,
			"low_month": low_month
		},
		"anomalies": {
			str(date): float(value) 
			for date, value in anomalies.items()
		}
	}

def get_comparative_analysis(df: pd.DataFrame, metric_name: str) -> dict:
	"""Vergleicht aktuelle Werte mit historischen Daten."""
	if metric_name not in df.columns:
		raise ValueError(f"Metrik {metric_name} nicht in DataFrame gefunden")
	
	data = df[metric_name].dropna()
	
	# Vergleich mit Vorjahr
	current_year = data.index.max().year
	last_year = current_year - 1
	
	current_year_data = data[data.index.year == current_year]
	last_year_data = data[data.index.year == last_year]
	
	# Berechne year-over-year Änderung
	if not last_year_data.empty and not current_year_data.empty:
		yoy_change = ((current_year_data.mean() - last_year_data.mean()) 
					  / last_year_data.mean() * 100)
	else:
		yoy_change = None
	
	return {
		"year_over_year": {
			"current_year_avg": float(current_year_data.mean()) if not current_year_data.empty else None,
			"last_year_avg": float(last_year_data.mean()) if not last_year_data.empty else None,
			"change_percent": float(yoy_change) if yoy_change is not None else None
		}
	}