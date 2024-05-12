from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
import energy_util as util
import io
from flask import send_file, jsonify


app = Flask(__name__)
app.secret_key = 'dein_sehr_geheimer_schlüssel'



@app.route('/api/data/<resource_type>', methods=['GET'])
def api_data(resource_type):
	try:
		df = util.get_data_for_type(resource_type)  # This should fetch DataFrame with 'datum' as index
		
		# Convert the index to a list of strings (for labels) and extract data values
		labels = df.index.strftime('%Y-%m-%d').tolist()  # Format dates as strings
		data_values = df[resource_type].tolist()  # Assuming data for plotting is in a column named after the resource type

		# Format the data as expected by Chart.js
		formatted_data = {
			"labels": labels,
			"data": data_values
		}
		
		return jsonify(formatted_data)
	except Exception as e:
		# Handle errors and provide useful error messages
		return jsonify({'error': str(e)}), 500




@app.route('/graphs', defaults={'type': 'all'})
@app.route('/graphs/<type>', methods=['GET'])
def graphs(type):
	data = {}  # Here, you would fetch the data based on the type
	try:
		if type == 'all':
			data = util.prepare_all_data()
		else:
			data = util.get_data_for_type(type)
	except Exception as e:
		flash(f"Error loading data for {type}: {str(e)}", "error")
		print(e)
		return redirect(url_for('home'))

	return render_template('graphs.html', active_page='graphs', active_sub_tab=type, data=data)

@app.route('/', methods=['GET'])
def home():
	today = datetime.now().strftime('%Y-%m-%d')
	try:
		data = util.prepare_data_for_list_display()
	except pd.errors.EmptyDataError:
		data = pd.DataFrame().to_dict(orient='records')
		flash("Keine Daten vorhanden.", "error")
	except Exception as e:
		print(e)
		data = pd.DataFrame().to_dict(orient='records')
		flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
	return render_template('home.html', today=today, data=data, active_page='home')

@app.route('/submit', methods=['POST'])
def submit():
	try:
		datum = request.form['datum']
		formatted_date = util.format_date_for_storage(datum)  # Convert to storage format
		# Check date validity
		if not (2000 <= int(formatted_date[:4]) <= 2100):
			raise ValueError("Invalid year.")
	except ValueError as e:
		print(e)
		flash(f'Fehler beim Eintragen der Daten: {str(e)}', 'error')
		return redirect(url_for('home'))
	
	new_data = {
		'datum': formatted_date,
		'strom': request.form['strom'],
		'wasser': request.form['wasser'],
		'gas': request.form['gas'],
		'dle': request.form['dle'],
		'einspeisung': request.form['einspeisung'],
		'garten': request.form['garten']
	}

	try:
		df = util.get_data()
		date_timestamp = pd.Timestamp(formatted_date)  # Convert to pd.Timestamp for comparison
		if date_timestamp in df.index:
			flash('Warnung: Ein Eintrag für dieses Datum existiert bereits. Er wurde überschrieben.', 'warning')
			df = df.drop(date_timestamp)
		df.loc[date_timestamp] = pd.Series(new_data)
		util.save_data(df)
		flash(f'Erfolgreich eingetragen: {str(df.loc[date_timestamp])}', 'success')
	except Exception as e:
		print(e)
		flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
	return redirect(url_for('home'))


@app.route('/delete', methods=['POST'])
def delete_entry():
	try:
		# Convert the input string directly to pd.Timestamp and normalize it to remove time
		date_to_delete = pd.Timestamp(pd.to_datetime(request.form['date_to_delete'], format='%d.%m.%Y').date())

		df = util.get_data()
	
		# Drop expects the exact type as the DataFrame index
		if date_to_delete in df.index:
			df.drop(date_to_delete, inplace=True)  # Use the pd.Timestamp directly
			util.save_data(df)
			flash(f'Eintrag für {date_to_delete.strftime("%d.%m.%Y")} erfolgreich gelöscht', 'success')
		else:
			flash(f'Datum {date_to_delete.strftime("%d.%m.%Y")} nicht gefunden', 'error')

	except Exception as e:
		flash(f'Fehler beim Löschen des Datums: {str(e)}', 'error')

	return redirect(url_for('home'))

@app.route('/check_date', methods=['POST'])
def check_date():
	datum = request.form['datum']
	formatted_date = util.format_date_for_storage(datum)
	
	try:
		df = util.get_data()
		date_timestamp = pd.Timestamp(formatted_date)
		if date_timestamp in df.index:
			return jsonify({'exists': True})
		else:
			return jsonify({'exists': False})
	except Exception as e:
		return jsonify({'error': str(e)}), 500


@app.route('/api/data/<resource_type>/<timeframe>')
def get_resource_data(resource_type, timeframe):
	try:
		data, yearly_data = util.prepare_data_for_graphs(resource_type, timeframe)
		return jsonify({
			'data': data.to_dict(orient='records'),
			'yearly_data': yearly_data
		})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_data():
	try:
		df = util.get_data()  # Assuming util.get_data() returns the current DataFrame
		df.index = df.index.strftime('%Y-%m-%d')
		today = datetime.now().strftime('%Y-%m-%d')
		filename = f"energie_{today}.xlsx"

		# Convert DataFrame to Excel
		output = io.BytesIO()
		with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
			df.to_excel(writer, index=True, sheet_name='Data')

			# Get the xlsxwriter workbook and worksheet objects.
			workbook  = writer.book
			worksheet = writer.sheets['Data']
			
			# Add a header format.
			header_format = workbook.add_format({
				'bold': True,
				'text_wrap': True,
				'valign': 'top',
				'fg_color': '#D7E4BC',
				'border': 1})

			# Write the column headers with the defined format.
			for col_num, value in enumerate(df.columns):
				worksheet.write(0, col_num + 1, value, header_format)
			worksheet.write(0, 0, 'Datum', header_format)

			# Set the column width to make the content more readable.
			worksheet.set_column('A:A', 15)
			for i, column in enumerate(df.columns, start=1):
				worksheet.set_column(i, i, 15)
			
			# Freeze the header row.
			worksheet.freeze_panes(1, 0)

			# Add autofilter.
			worksheet.autofilter(0, 0, len(df), len(df.columns))
		
		output.seek(0)
		
		return send_file(
			output,
			mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
			as_attachment=True,
			download_name=filename
		)
	except Exception as e:
		flash(f"Fehler beim Erstellen der Excel-Datei: {str(e)}", "error")
		return redirect(url_for('home'))


@app.route('/api/graph_data/strom', methods=['GET'])
def api_graph_data_strom():
    try:
        accumulated, consumption_diff, monthly_avg = util.get_strom_data()
        
        response_data = {
            'accumulated': accumulated.to_dict(orient='records'),
            'consumption_diff': consumption_diff.to_dict(orient='records'),
            'monthly_avg': monthly_avg.to_dict(orient='records'),
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
