from flask import Flask
from routes.podcast_routes import podcast_bp
from datetime import date

app = Flask(__name__)
app.register_blueprint(podcast_bp)

@app.context_processor
def inject_today():
    return dict(today=date.today())

if __name__ == "__main__":
    app.run(debug=True, port=5010)
