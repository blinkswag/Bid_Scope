# app/views/bot_settings_views.py

from flask import render_template, request, redirect, url_for, jsonify
from app.utils.helpers import check_user_role
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv('API_KEY'))
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

def init_bot_settings_views(app):
    @app.route('/bot-settings', methods=['GET', 'POST'])
    @check_user_role(['Super Admin'])
    def bot_settings():
        if request.method == 'POST':
            update_data = {}
            if 'name' in request.form:
                update_data['name'] = request.form['name']
            if 'description' in request.form:
                update_data['description'] = request.form['description']
            if 'instructions' in request.form:
                update_data['instructions'] = request.form['instructions']
            if 'model' in request.form:
                update_data['model'] = request.form['model']
            if 'temperature' in request.form:
                update_data['temperature'] = float(request.form['temperature'])
            
            try:
                client.beta.assistants.update(ASSISTANT_ID, **update_data)
                return redirect(url_for('bot_settings'))
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        my_assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
        return render_template('bot_settings.html', assistant=my_assistant)
