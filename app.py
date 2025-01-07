from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
import flask.cli  # Import CLI utilities
import csv
import time
import random

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

# StockPrice model
class StockPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)

# Log user actions to CSV
def log_action(username, action, ticker, quantity, capital_before, capital_after):
    with open("trading_logs.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([username, time.strftime("%Y-%m-%d %H:%M:%S"), action, ticker, quantity, capital_before, capital_after])

# Update stock prices
def update_stock_prices():
    stocks = StockPrice.query.all()
    for stock in stocks:
        change = random.uniform(-0.1, 0.1)  # -10% to +10%
        stock.price = round(stock.price * (1 + change), 2)
    db.session.commit()

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

    # Update stock prices for the round
    update_stock_prices()

    # Fetch updated prices
    prices = {stock.ticker: stock.price for stock in StockPrice.query.all()}

    return render_template("trade.html", username=username, capital=user.capital, prices=prices)

@app.route("/action", methods=["POST"])
def action():
    data = request.json
    print(data)  # Log the incoming data for debugging
    username = data.get("username")
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = data.get("quantity")

    if not all([username, action, ticker, quantity]):
        return jsonify({"error": "Missing data"}), 400

    # Get user and validate ticker
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "Unauthorized user"}), 403

    stock = StockPrice.query.filter_by(ticker=ticker).first()
    if not stock:
        return jsonify({"error": "Invalid ticker symbol"}), 400

    price = stock.price
    capital_before = user.capital

    # Update user capital
    if action == "Buy":
        cost = price * quantity
        if capital_before >= cost:
            user.capital -= cost
        else:
            return jsonify({"error": "Insufficient funds"}), 400
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

    # Add initial stock prices
    initial_prices = {
        "MSFT": 100,
        "AAPL": 120,
        "GOOG": 150,
        "TSLA": 200
    }
    for ticker, price in initial_prices.items():
        stock = StockPrice(ticker=ticker, price=price)
        db.session.add(stock)

    db.session.commit()
    print("Database initialized successfully.")

if __name__ == "__main__":
    app.run(debug=True)
    