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

def format_date_for_display(date_str):
    """ Convert date from YYYY-MM-DD to DD.MM.YYYY format for display purposes. """
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m.%Y')

def format_date_for_storage(date_str):
    """ Convert date from DD.MM.YYYY to YYYY-MM-DD format for storage purposes. """
    return datetime.strptime(date_str, '%d.%m.%Y').strftime('%Y-%m-%d')

def get_data():
    """ Retrieve and format data from a CSV file. """
    csv_file_path = get_data_file_path()
    df = pd.read_csv(csv_file_path, delimiter=';', decimal=',', index_col=False)
    df[csv_data_columns] = df[csv_data_columns].apply(pd.to_numeric, errors='coerce')
    df[csv_data_columns] = df[csv_data_columns].apply(np.floor).astype('Int64')
    return df

def save_data(df: pd.DataFrame, sep=';', decimal=','):
    csv_file_path = get_data_file_path()
    """ Save data to a CSV file, using the specified delimiter and decimal format. """
    df.to_csv(csv_file_path, index=False, sep=sep, decimal=decimal)

def get_data_file_path():
	""" Return the path to the CSV data file. """
	# data csv if on windows, /var/www/data.csv if on linux
	if os.name == 'nt':
		return 'data.csv'
	else:
		return '/var/www/energy/bach_energy.csv'

def prepare_data_for_list_display():
	""" Prepare data for display in a list format. """
	df = get_data()
	df['datum'] = df['datum'].apply(format_date_for_display)
	df.rename(columns=df_renames_display, inplace=True)
	df = df.iloc[::-1] # flip the table bottom to top
	return df.to_dict(orient='records')
