# energy_util.py
import pandas as pd
from datetime import datetime
import numpy as np
import os

csv_data_columns = ['strom', 'wasser', 'gas', 'dle', 'einspeisung', 'garten'] 

df_renames_display = {
	'dle': 'DLE',
	'einspeisung': 'Einspeisung',
	'gas': 'Gas',
	'strom': 'Strom',
	'wasser': 'Wasser',
	'garten': 'Garten',
	'datum': 'Datum'
}

def format_date_for_display(date_input):
	""" Convert date from various formats to DD.MM.YYYY format for display purposes.
		Handles pd.Timestamp, datetime, and string inputs.
	"""
	# If the input is a string, assume it's in YYYY-MM-DD format and convert it
	if isinstance(date_input, str):
		try:
			date_input = datetime.strptime(date_input, '%Y-%m-%d')
		except ValueError:
			raise ValueError("Date string must be in YYYY-MM-DD format")
	
	# Check if the input is a pd.Timestamp or datetime after potential conversion
	if isinstance(date_input, (pd.Timestamp, datetime)):
		return date_input.strftime('%d.%m.%Y')
	else:
		raise TypeError("Input must be a string, pd.Timestamp, or datetime object")


def format_date_for_storage(date_str):
	""" Convert date from DD.MM.YYYY format to YYYY-MM-DD format for storage purposes. """
	try:
		return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
	except ValueError:
		raise ValueError("Date string must be in DD.MM.YYYY format")


def save_data(df: pd.DataFrame, sep=';', decimal=','):
	csv_file_path = get_data_file_path()
	""" Save data to a CSV file, using the specified delimiter and decimal format. """
	df.to_csv(csv_file_path, index=True, sep=sep, decimal=decimal)

def get_data_file_path():
	""" Return the path to the CSV data file. """
	# data csv if on windows, /var/www/data.csv if on linux
	if os.name == 'nt':
		return 'data.csv'
	else:
		return '/var/www/data/bach_energy_data.csv'

def get_data():
	""" Retrieve and format data from a CSV file. """
	csv_file_path = get_data_file_path()
	df = pd.read_csv(csv_file_path, delimiter=';', decimal=',', parse_dates=['datum'])
	df['datum'] = pd.to_datetime(df['datum']).dt.normalize()  # Normalize to remove time part
	df.set_index('datum', inplace=True)
	df[csv_data_columns] = df[csv_data_columns].apply(pd.to_numeric, errors='coerce')
	df[csv_data_columns] = df[csv_data_columns].apply(np.floor).astype('Int64')
	return df

def prepare_data_for_list_display():
	""" Prepare data for display in a list format. """
	df = get_data()
	df_reset = df.reset_index()  # Reset index to manipulate 'datum' as a column
	# Apply date formatting
	df_reset['datum'] = df_reset['datum'].apply(format_date_for_display)
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
    types = ['strom', 'wasser', 'gas', 'dle', 'einspeisung', 'garten']
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
		data['year'] = data.index.year
		data['month'] = data.index.month
		yearly_data = data.pivot_table(index='month', columns='year', values=resource_type)

		return data, yearly_data.to_dict()

	return data
