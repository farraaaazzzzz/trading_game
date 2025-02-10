from flask import Flask, render_template, request, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import os
import csv
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

migrate = Migrate(app, db) # Initialize the Migrate object

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    capital = db.Column(db.Float, default=100000.0)

# User holdings model
class UserHoldings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref=db.backref('holdings', lazy=True))

# Game configuration: Fixed stock prices & hidden ROI percentages
STOCK_PRICES = [
    {
        "MSFT": {"price": 100, "image": "/static/turn1/MSFT.png", "roi": 0.5},
        "AAPL": {"price": 120, "image": "/static/turn1/AAPL.png", "roi": 0.98},
        "GOOG": {"price": 150, "image": "/static/turn1/GOOG.png", "roi": 1.02},
        "TSLA": {"price": 200, "image": "/static/turn1/TSLA.png", "roi": 0.40},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn2/MSFT.png", "roi": 0.3},
        "AAPL": {"price": 130, "image": "/static/turn2/AAPL.png", "roi": 0.5},
        "GOOG": {"price": 140, "image": "/static/turn2/GOOG.png", "roi": 0.6},
        "TSLA": {"price": 210, "image": "/static/turn2/TSLA.png", "roi": 2.4},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn3/MSFT.png", "roi": 2.4},
        "AAPL": {"price": 130, "image": "/static/turn3/AAPL.png", "roi": 0.5},
        "GOOG": {"price": 140, "image": "/static/turn3/GOOG.png", "roi": 0.02},
        "TSLA": {"price": 210, "image": "/static/turn3/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn4/MSFT.png", "roi": 4.5},
        "AAPL": {"price": 130, "image": "/static/turn4/AAPL.png", "roi": 4.2},
        "GOOG": {"price": 140, "image": "/static/turn4/GOOG.png", "roi": 4.3},
        "TSLA": {"price": 210, "image": "/static/turn4/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn5/MSFT.png", "roi": 0.2},
        "AAPL": {"price": 130, "image": "/static/turn5/AAPL.png", "roi": 0.35},
        "GOOG": {"price": 140, "image": "/static/turn5/GOOG.png", "roi": 2.9},
        "TSLA": {"price": 210, "image": "/static/turn5/TSLA.png", "roi": 1.38},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn6/MSFT.png", "roi": 1.45},
        "AAPL": {"price": 130, "image": "/static/turn6/AAPL.png", "roi": 1.25},
        "GOOG": {"price": 140, "image": "/static/turn6/GOOG.png", "roi": 0.65},
        "TSLA": {"price": 210, "image": "/static/turn6/TSLA.png", "roi": 0.8},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn7/MSFT.png", "roi": 1.04},
        "AAPL": {"price": 130, "image": "/static/turn7/AAPL.png", "roi": 1.01},
        "GOOG": {"price": 140, "image": "/static/turn7/GOOG.png", "roi": 1.03},
        "TSLA": {"price": 210, "image": "/static/turn7/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn8/MSFT.png", "roi": 1.04},
        "AAPL": {"price": 130, "image": "/static/turn8/AAPL.png", "roi": 1.01},
        "GOOG": {"price": 140, "image": "/static/turn8/GOOG.png", "roi": 1.03},
        "TSLA": {"price": 210, "image": "/static/turn8/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn9/MSFT.png", "roi": 0.25},
        "AAPL": {"price": 130, "image": "/static/turn9/AAPL.png", "roi": 0.12},
        "GOOG": {"price": 140, "image": "/static/turn9/GOOG.png", "roi": 9.13},
        "TSLA": {"price": 210, "image": "/static/turn9/TSLA.png", "roi": 1.2},
    },
    {
        "MSFT": {"price": 110, "image": "/static/turn10/MSFT.png", "roi": 0.14},
        "AAPL": {"price": 130, "image": "/static/turn10/AAPL.png", "roi": 0.12},
        "GOOG": {"price": 140, "image": "/static/turn10/GOOG.png", "roi": 0.05},
        "TSLA": {"price": 210, "image": "/static/turn10/TSLA.png", "roi": 0.02},
    },
]

# Initialize CSV for trade logs
LOG_FILE = "trading_log.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "username", "turn", "action", "ticker", "quantity", "capital_before", "capital_after"])
        
@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.first():
            db.session.add(User(username="user1", password="password1"))
            db.session.commit()
    print("Database initialized.")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            # Reset user capital
            user.capital = 100000.0

            # Reset user holdings
            existing_holdings = UserHoldings.query.filter_by(user_id=user.id).all()
            for holding in existing_holdings:
                holding.quantity = 0

            db.session.commit()

            # Update CSV header
            with open(LOG_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "timestamp", "username", "turn", "action", "ticker",
                    "quantity", "capital_before", "capital_after", "portfolio_value"
                ])


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
    holdings = {holding.ticker: holding.quantity for holding in user.holdings}

    # Calculate portfolio value
    portfolio_value = sum(
        holdings.get(ticker, 0) * stock_data[ticker]["price"]
        for ticker in stock_data
    )

    print(f"[DEBUG] User: {username}, Turn: {turn + 1}, Holdings: {holdings}, Portfolio Value: {portfolio_value}")
    
    return render_template(
        "trade.html",
        username=username,
        capital=user.capital,
        stock_data=stock_data,
        holdings=holdings,
        portfolio_value=portfolio_value,
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
    holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()
    stock = STOCK_PRICES[session.get("turn", 0)].get(ticker, {})
    price = stock.get("price", 100)
    
    capital_before = user.capital

    if action == "Buy":
        cost = price * quantity
        if user.capital >= cost:
            user.capital -= cost
            if holding:
                holding.quantity += quantity
            else:
                holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=quantity)
                db.session.add(holding)
        else:
            return jsonify({"error": "Insufficient funds"}), 400
    elif action == "Sell":
        if holding and holding.quantity >= quantity:
            user.capital += price * quantity
            holding.quantity -= quantity
        else:
            return jsonify({"error": "Not enough shares to sell"}), 400
    
    # Calculate portfolio value after the action
    holdings = {h.ticker: h.quantity for h in user.holdings}
    stock_data = STOCK_PRICES[session.get("turn", 0)]
    portfolio_value = sum(
        holdings.get(ticker, 0) * stock_data[ticker]["price"]
        for ticker in stock_data
    )

    # Debug log for the action
    print(f"[DEBUG] User: {username}, Action: {action}, Ticker: {ticker}, Quantity: {quantity}")
    print(f"[DEBUG] Capital Before: {capital_before}, Capital After: {user.capital}, Portfolio Value: {portfolio_value}")

    capital_after = user.capital
    db.session.commit()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, username, session.get("turn", 0) + 1, action, ticker, quantity,
            capital_before, capital_after, portfolio_value
        ])
    
    return jsonify({"capital": user.capital, "portfolio": portfolio_value})

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
    stock_data = STOCK_PRICES[turn]
    
    for holding in user.holdings:
        roi = stock_data.get(holding.ticker, {}).get("roi", 1.0)
        user.capital += holding.quantity * stock_data[holding.ticker]["price"] * (roi - 1)

    # Recalculate portfolio value for the new turn
    holdings = {h.ticker: h.quantity for h in user.holdings}
    portfolio_value = sum(
        holdings.get(ticker, 0) * stock_data[ticker]["price"]
        for ticker in stock_data
    )
    
    # Debug log for new turn
    print(f"[DEBUG] User: {username}, New Turn: {session['turn'] + 1}")
    print(f"[DEBUG] Updated Capital: {user.capital}, Portfolio Value: {portfolio_value}")
    
    db.session.commit()
    return jsonify({"message": "Next turn started", "capital": user.capital, "portfolio": portfolio_value}) 

# Add the remaining function definitions (login, trade, action, etc.)
if __name__ == "__main__":
    app.run(debug=True)