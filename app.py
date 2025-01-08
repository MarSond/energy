from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
import pandas as pd
from datetime import datetime
import io
import energy_util as util
from constants import *
from constants import ENERGY_TYPES, STROM

app = Flask(__name__)
app.secret_key = 'dein_sehr_geheimer_schlüssel'  # In der Produktion sollte dies sicher gespeichert werden

@app.route('/', methods=['GET'])
def home():
    today = datetime.now().strftime(DATE_STR_DASH)
    try:
        data = util.prepare_data_for_list_display()
    except Exception as e:
        data = []
        flash(f"Fehler beim Laden der Daten: {str(e)}", "error")
    return render_template('home.html', today=today, data=data, active_page='home')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        datum = request.form[DATUM]
        formatted_date = util.format_date_for_storage(datum)
        
        # Überprüfe Datumsvalidität
        current_year = datetime.now().year
        if not (2000 <= int(formatted_date[:4]) <= current_year):
            raise ValueError(f"Ungültiges Jahr. Bitte geben Sie ein Jahr zwischen 2000 und {current_year} ein.")
        
        new_data = {
            DATUM: formatted_date,
            STROM: request.form[STROM],
            WASSER: request.form[WASSER],
            GAS: request.form[GAS],
            DLE: request.form[DLE],
            EINSPEISUNG: request.form[EINSPEISUNG],
            GARTEN: request.form[GARTEN]
        }
        
        # Validiere numerische Eingaben
        for key, value in new_data.items():
            if key != DATUM and value.strip():
                try:
                    float(value)
                except ValueError:
                    raise ValueError(f"Ungültige Eingabe für {key}. Bitte geben Sie einen numerischen Wert ein.")
        
        df = util.get_data()
        date_timestamp = pd.Timestamp(formatted_date)
        
        if date_timestamp in df.index:
            flash('Warnung: Ein Eintrag für dieses Datum existiert bereits. Er wurde überschrieben.', 'warning')
            df = df.drop(date_timestamp)
        
        df.loc[date_timestamp] = pd.Series(new_data)
        util.save_data(df)
        
        flash(f'Erfolgreich eingetragen: {", ".join([f"{k}: {v}" for k, v in new_data.items() if v.strip()])}', 'success')
    
    except ValueError as e:
        flash(f'Fehler beim Eintragen der Daten: {str(e)}', 'error')
    except Exception as e:
        flash(f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}", "error")
    
    return redirect(url_for('home'))

@app.route('/delete', methods=['POST'])
def delete_entry():
    try:
        date_to_delete_str = request.form[DATE_TO_DELETE]
        app.logger.info(f"Received date to delete: {date_to_delete_str}")
        
        # Konvertiere das Datum in das Format YYYY-MM-DD
        date_to_delete = util.format_date_for_storage(date_to_delete_str)
        app.logger.info(f"Formatted date for storage: {date_to_delete}")

        df = util.get_data()
        app.logger.info(f"DataFrame index: {df.index}")
    
        if date_to_delete in df.index:
            df.drop(date_to_delete, inplace=True)
            util.save_data(df)
            flash(f'Eintrag für {util.format_date_for_display(date_to_delete)} erfolgreich gelöscht', 'success')
        else:
            app.logger.warning(f"Date {date_to_delete} not found in index")
            flash(f'Datum {util.format_date_for_display(date_to_delete)} nicht gefunden', 'error')

    except Exception as e:
        app.logger.error(f"Error in delete_entry: {str(e)}")
        flash(f'Fehler beim Löschen des Datums: {str(e)}', 'error')

    return redirect(url_for('home'))

@app.route('/graphs')
@app.route('/graphs/<energy_type>')
def graphs(energy_type=STROM):
    if energy_type not in ENERGY_TYPES:
        energy_type = STROM
    return render_template('graphs.html', active_page='graphs', active_energy_type=energy_type, energy_types=ENERGY_TYPES)

@app.route('/api/data/<energy_type>')
def api_data(energy_type):
    if energy_type not in ENERGY_TYPES:
        return jsonify({'error': 'Ungültiger Energietyp'}), 400
    
    try:
        df = util.get_data(apply_corrections=True)
        if energy_type not in df.columns:
            return jsonify({'error': 'Daten nicht verfügbar'}), 404
        
        data = df[[energy_type]].dropna().sort_index()
        
        return jsonify({
            'labels': data.index.strftime('%Y-%m-%d').tolist(),
            'values': data[energy_type].tolist()
        })
    except Exception as e:
        app.logger.error(f"Fehler beim Abrufen der Daten für {energy_type}: {str(e)}")
        return jsonify({'error': 'Interner Serverfehler'}), 500


@app.route('/check_date', methods=['POST'])
def check_date():
    try:
        datum = request.form[DATUM]
        formatted_date = util.format_date_for_storage(datum)
        df = util.get_data()
        exists = formatted_date in df.index
        return jsonify({'exists': exists})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['GET'])
def download_data():
    try:
        df = util.get_data()
        df.index = df.index.strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"energie_{today}.xlsx"

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=True, sheet_name='Data')

            workbook = writer.book
            worksheet = writer.sheets['Data']
            
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1})

            for col_num, value in enumerate(df.columns):
                worksheet.write(0, col_num + 1, value, header_format)
            worksheet.write(0, 0, 'Datum', header_format)

            worksheet.set_column('A:A', 15)
            for i, column in enumerate(df.columns, start=1):
                worksheet.set_column(i, i, 15)
            
            worksheet.freeze_panes(1, 0)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)