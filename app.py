from flask import Flask, render_template, request, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import os
import csv
from datetime import datetime  # Import at the top of the file

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)  # Needed for session management
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    capital = db.Column(db.Float, default=100000.0)

# Game configuration: Headlines and stock prices with images
HEADLINES = [
    "MSFT announces record earnings!",
    "AAPL unveils a revolutionary product.",
    "GOOG faces government investigation.",
    "TSLA launches a new electric vehicle.",
    "MSFT acquires a leading AI company.",
    "AAPL's new iPhone dominates sales.",
    "GOOG integrates AI into search engines.",
    "TSLA develops innovative battery technology.",
    "MSFT collaborates with major tech companies.",
    "AAPL rumored to enter the automotive market."
]

STOCK_PRICES = [
    {
        "MSFT": {"price": 100, "image": "/static/turn1/MSFT.png"},
        "AAPL": {"price": 120, "image": "/static/turn1/AAPL.png"},
        "GOOG": {"price": 150, "image": "/static/turn1/GOOG.png"},
        "TSLA": {"price": 200, "image": "/static/turn1/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn2/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn2/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn2/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn2/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn3/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn3/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn3/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn3/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn4/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn4/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn4/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn4/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn5/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn5/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn5/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn5/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn6/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn6/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn6/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn6/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn7/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn7/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn7/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn7/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn8/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn8/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn8/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn8/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn9/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn9/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn9/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn9/TSLA.png"},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn10/MSFT.png"},
        "AAPL": {"price": 130, "image": "/static/turn10/AAPL.png"},
        "GOOG": {"price": 140, "image": "/static/turn10/GOOG.png"},
        "TSLA": {"price": 210, "image": "/static/turn10/TSLA.png"},
    },
]

# Initialize CSV for trade logs
LOG_FILE = "trading_log.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["username", "turn", "action", "ticker", "quantity", "capital_before", "capital_after"])

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            user.capital = 100000.0  # Reset capital on login
            db.session.commit()
            session["username"] = username
            session["turn"] = 0  # Reset the turn
            return redirect("/trade")
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route("/trade")
def trade():
    username = session.get("username")
    if not username:
        return redirect("/")
    
    turn = session.get("turn", 0)
    if turn >= len(STOCK_PRICES):
        return "Game Over! Thank you for playing."

    stock_data = STOCK_PRICES[turn]
    user = User.query.filter_by(username=username).first()
    return render_template(
        "trade.html",
        username=username,
        capital=user.capital,
        stock_data=stock_data,
        headline=HEADLINES[turn],
        turn=turn + 1
    )

@app.route("/action", methods=["POST"])
def action():
    data = request.json
    username = data.get("username")
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = int(data.get("quantity", 0))

    user = User.query.filter_by(username=username).first()
    turn = session.get("turn", 0)
    if not user or turn >= len(STOCK_PRICES):
        return jsonify({"error": "Invalid user or game over"}), 400

    prices = STOCK_PRICES[turn]
    stock = prices.get(ticker)
    if not stock:
        return jsonify({"error": "Invalid ticker"}), 400

    price = stock["price"]
    capital_before = user.capital

    # Process the action
    if action == "Buy":
        cost = price * quantity
        if capital_before >= cost:
            user.capital -= cost
        else:
            return jsonify({"error": "Insufficient funds"}), 400
    elif action == "Sell":
        user.capital += price * quantity

    capital_after = user.capital
    db.session.commit()

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log the trade to CSV with the timestamp
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, username, turn + 1, action, ticker, quantity, 
            capital_before, capital_after
        ])

    return jsonify({"capital": user.capital})

@app.route("/next-turn", methods=["POST"])
def next_turn():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 400

    turn = session.get("turn", 0)
    if turn >= len(STOCK_PRICES) - 1:
        return jsonify({"message": "Game Over"}), 200

    session["turn"] += 1
    user = User.query.filter_by(username=username).first()
    return jsonify({
        "message": "Next turn started",
        "capital": user.capital
    })

@app.cli.command("init-db")
def init_db():
    db.create_all()
    if not User.query.first():
        db.session.add(User(username="user1", password="password1"))
        db.session.commit()
    print("Database initialized.")

if __name__ == "__main__":
    app.run(debug=True)
