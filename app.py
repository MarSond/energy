from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
from datetime import datetime
import numpy as np

app = Flask(__name__)
app.secret_key = 'dein_sehr_geheimer_schlüssel'
csv_file_path = 'data.csv'  # Pfad zur CSV-Datei
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

@app.route('/', methods=['GET'])
def home():
    today = datetime.now().strftime('%Y-%m-%d')   # Heutiges Datum im deutschen Format
    try:
        df = get_data()
        df['datum'] = pd.to_datetime(df['datum'], format='%Y-%m-%d').dt.strftime('%d.%m.%Y')  # Datum im deutschen Format anzeigen
        df = df.iloc[::-1] # flip the table bottom to top
        data_html = df.rename(columns=df_renames_display).to_html(classes='data-table', table_id="data_table", border=0, index=False)
        
    except pd.errors.EmptyDataError:
        data_html = "<p>Keine Daten vorhanden.</p>"
    except Exception as e:
        flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
        data_html = "<p>Fehler beim Laden der Daten.</p>"
    return render_template('home.html', today=today, table=data_html)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        datum = datetime.strptime(request.form['datum'], '%Y-%m-%d').strftime('%Y-%m-%d')  # Datum aus dem Formular im ISO-Format umwandeln
        # check if datum is before 2000
        if int(datum[:4]) < 2000 or int(datum[:4]) > 2100:
            raise ValueError
    except ValueError:
        flash('Fehler beim Eintragen der Daten: Ungültiges Datum', 'error')
        return redirect(url_for('home'))
    new_data = {
        'datum': datum,  # Das Datum wird direkt als String genutzt
        'strom': request.form['strom'],
        'wasser': request.form['wasser'],
        'gas': request.form['gas'],
        'dle': request.form['dle'],
        'einspeisung': request.form['einspeisung'],
        'garten': request.form['garten']
    }

    try:
        df = get_data()
        if datum in df['datum'].values:
            flash(f'Warnung: Ein Eintrag für dieses Datum existiert bereits. Er wird überschrieben. Alte Daten waren: id {str(df[df['datum'] == datum])}', 'warning')
            df = df[df['datum'] != datum]  # Vorhandenen Eintrag entfernen
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)  
        save_data(df)
        flash('Erfolgreich eingetragen', 'success')
    except Exception as e:
        flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
    return redirect(url_for('home'))

def save_data(df):
    df.to_csv(csv_file_path, index=False, sep=';')

def get_data():
    df = pd.read_csv(csv_file_path, delimiter=';', decimal=',', index_col=False)
    df[csv_data_columns] = df[csv_data_columns].apply(pd.to_numeric, errors='coerce')
    df[csv_data_columns] = df[csv_data_columns].apply(np.floor).astype('Int64')
    return df

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)