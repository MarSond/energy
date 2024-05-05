from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
import energy_util as util

app = Flask(__name__)
app.secret_key = 'dein_sehr_geheimer_schlüssel'

@app.route('/graphs/', methods=['GET'])


@app.route('/graphs', defaults={'type': 'all'})
@app.route('/graphs/<type>', methods=['GET'])
def graphs(type):
	data = {}  # Here, you would fetch the data based on the type
	try:
		if type == 'all':
			data = util.prepare_all_data()
		else:
			data = util.prepare_data_for_type(type)
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
			flash('Warnung: Ein Eintrag für dieses Datum existiert bereits. Er wird überschrieben.', 'warning')
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


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000)
