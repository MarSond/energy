from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
import energy_util as util

app = Flask(__name__)
app.secret_key = 'dein_sehr_geheimer_schlüssel'


@app.route('/', methods=['GET'])
def home():
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        data = util.prepare_data_for_list_display()
    except pd.errors.EmptyDataError:
        data = pd.DataFrame().to_dict(orient='records')
        flash("Keine Daten vorhanden.", "error")
    except Exception as e:
        data = pd.DataFrame().to_dict(orient='records')
        flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
    return render_template('home.html', today=today, data=data)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        datum = request.form['datum']
        formatted_date = util.format_date_for_storage(datum)  # Convert to storage format
        # Check date validity
        if not (2000 <= int(formatted_date[:4]) <= 2100):
            raise ValueError("Invalid year.")
    except ValueError as e:
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
        if formatted_date in df['datum'].values:
            flash('Warnung: Ein Eintrag für dieses Datum existiert bereits. Er wird überschrieben.', 'warning')
            df = df[df['datum'] != formatted_date]  # Remove existing entry
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        util.save_data(df)
        flash('Erfolgreich eingetragen', 'success')
    except Exception as e:
        flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
    return redirect(url_for('home'))

@app.route('/delete', methods=['POST'])
def delete_entry():
    date_to_delete = request.form['date_to_delete']
    try:
        df = util.get_data()
        df = df[df['datum'] != util.format_date_for_storage(date_to_delete)]
        util.save_data(df)
        flash(f'Eintrag {str(date_to_delete)} erfolgreich gelöscht', 'success')
    except Exception as e:
        flash(f'Fehler beim Löschen des Datums: {str(e)}', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
