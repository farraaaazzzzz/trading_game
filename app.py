from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import flask.cli  # Import CLI utilities
import csv
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    capital = db.Column(db.Float, default=1000.0)

# Log user actions to CSV
def log_action(username, action, ticker, quantity, capital_before, capital_after):
    with open("trading_logs.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([username, time.strftime("%Y-%m-%d %H:%M:%S"), action, ticker, quantity, capital_before, capital_after])

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Authenticate user
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            return redirect(f"/trade/{username}")
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/trade/<username>")
def trade(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return "Unauthorized", 403
    return render_template("trade.html", username=username, capital=user.capital)

@app.route("/action", methods=["POST"])
def action():
    data = request.json
    username = data["username"]
    action = data["action"]
    ticker = data["ticker"]
    quantity = int(data["quantity"])

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "Unauthorized"}), 403

    capital_before = user.capital
    price = 100  # Fixed price for simplicity

    # Update user capital
    if action == "Buy":
        cost = price * quantity
        if capital_before >= cost:
            user.capital -= cost
    elif action == "Sell":
        user.capital += price * quantity

    db.session.commit()  # Save changes
    capital_after = user.capital

    # Log the action
    log_action(username, action, ticker, quantity, capital_before, capital_after)
    return jsonify({"capital": capital_after})

# CLI Command to initialize the database
@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized successfully.")

if __name__ == "__main__":
    app.run(debug=True)
