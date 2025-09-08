
from flask import Flask, redirect
from routes.podcast_routes import podcast_bp
from datetime import date
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.register_blueprint(podcast_bp)

@app.context_processor
def inject_today():
    return dict(today=date.today())

def jinja_strftime(value, fmt='%Y-%m-%d'):
    return value.strftime(fmt) if value else ''
app.jinja_env.filters['strftime'] = jinja_strftime

@app.route('/')
def home():
    return redirect('/calendar_view')

if __name__ == "__main__":
    app.run(debug=True, port=5010)
