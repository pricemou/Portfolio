import os
# Désactiver le chargement automatique du .env pour éviter les erreurs d'encodage
os.environ['FLASK_SKIP_DOTENV'] = '1'

from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@app.route('/works')
def works():
    """Page des réalisations"""
    current_year = datetime.now().year
    return render_template('works.html', current_year=current_year)

@app.route('/services')
def services():
    """Page des services"""
    current_year = datetime.now().year
    return render_template('services.html', current_year=current_year)

@app.route('/admin')
def admin():
    """Page d'administration"""
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)

