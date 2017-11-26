import os
from datetime import date
from googleplex import app
from .data import load_bestsellers
from .models import Bestseller, BestsellerList, Review
from flask import send_from_directory, render_template, request

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')

@app.route('/profile')
@app.route('/profile.html')
def profile():
    return render_template('profile.html')

@app.route('/submit')
@app.route('/submit.html')
def submit():
    return render_template('submit.html')

@app.route('/manual_submit')
@app.route('/manual_submit.html')
def manual_submit():
    return render_template('manual_submit.html')

@app.route('/preview')
@app.route('/preview.html')
def preview():
    return render_template('preview.html')

@app.route('/results')
@app.route('/results.html')
def results():
    search = request.args.get('search') or ''
    return render_template('results.html', lists=search_db(search), search=search)

def search_db(name):
    return [l for l in DATABASE_DATA if name.lower() in l.name.lower()]

DATABASE_DATA = load_bestsellers()
