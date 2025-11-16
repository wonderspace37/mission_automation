from flask import Flask, render_template
from generate_csv import generate_csv_bp
from generate_kml import generate_kml_bp

app = Flask(__name__)

app.register_blueprint(generate_csv_bp)
app.register_blueprint(generate_kml_bp)

@app.get("/")
def home():
    return render_template("index.html")
