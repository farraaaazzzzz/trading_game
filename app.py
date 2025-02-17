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

HEADLINES = [
    "MSFT announces record earnings, investors bullish! 🚀",
    "AAPL unveils a revolutionary product, market reacts! 📱",
    "GOOG faces government investigation over antitrust issues. ⚖️",
    "TSLA launches new self-driving feature, stocks surge! 🚗",
    "MSFT acquires OpenAI in a groundbreaking deal! 🤝",
    "AAPL's latest financial report beats expectations! 💰",
    "GOOG integrates next-gen AI into search engines! 🔍",
    "TSLA develops innovative battery tech, competitors worry! 🔋",
    "MSFT partners with top cloud providers for expansion! 📈",
    "AAPL rumored to enter the electric vehicle market! 🚗"
]

# Game configuration: Fixed stock prices & hidden ROI percentages
STOCK_PRICES = [
    {
        "MSFT": {"price": 100, "image": "/static/turn1/MSFT.png", "roi": 0.01},
        "AAPL": {"price": 100, "image": "/static/turn1/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 150, "image": "/static/turn1/GOOG.png", "roi": 1.02},
        "TSLA": {"price": 200, "image": "/static/turn1/TSLA.png", "roi": 0.40},
    },
    {
        "MSFT": {"price": 1, "image": "/static/turn2/MSFT.png", "roi": 9900},
        "AAPL": {"price": 110, "image": "/static/turn2/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn2/GOOG.png", "roi": 0.6},
        "TSLA": {"price": 210, "image": "/static/turn2/TSLA.png", "roi": 2.4},
    },
    {
        "MSFT": {"price": 100, "image": "/static/turn3/MSFT.png", "roi": 0.01},
        "AAPL": {"price": 121, "image": "/static/turn3/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn3/GOOG.png", "roi": 0.02},
        "TSLA": {"price": 210, "image": "/static/turn3/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 1, "image": "/static/turn4/MSFT.png", "roi": 9900},
        "AAPL": {"price": 133.1, "image": "/static/turn4/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn4/GOOG.png", "roi": 4.3},
        "TSLA": {"price": 210, "image": "/static/turn4/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 100, "image": "/static/turn5/MSFT.png", "roi": 0.9},
        "AAPL": {"price": 146.41, "image": "/static/turn5/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn5/GOOG.png", "roi": 2.9},
        "TSLA": {"price": 210, "image": "/static/turn5/TSLA.png", "roi": 1.38},
    },
    {
        "MSFT": {"price": 0, "image": "/static/turn6/MSFT.png", "roi": 0.9},
        "AAPL": {"price": 161.051, "image": "/static/turn6/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn6/GOOG.png", "roi": 0.65},
        "TSLA": {"price": 210, "image": "/static/turn6/TSLA.png", "roi": 0.8},
    },
    {
        "MSFT": {"price": 53.1441, "image": "/static/turn7/MSFT.png", "roi": 0.9},
        "AAPL": {"price": 177.1561, "image": "/static/turn7/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn7/GOOG.png", "roi": 1.03},
        "TSLA": {"price": 210, "image": "/static/turn7/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 47.82969, "image": "/static/turn8/MSFT.png", "roi": 0.9},
        "AAPL": {"price": 194.87171, "image": "/static/turn8/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn8/GOOG.png", "roi": 1.03},
        "TSLA": {"price": 210, "image": "/static/turn8/TSLA.png", "roi": 1.08},
    },
    {
        "MSFT": {"price": 43.046, "image": "/static/turn9/MSFT.png", "roi": 0.9},
        "AAPL": {"price": 171, "image": "/static/turn9/AAPL.png", "roi": 1.1},
        "GOOG": {"price": 140, "image": "/static/turn9/GOOG.png", "roi": 9.13},
        "TSLA": {"price": 210, "image": "/static/turn9/TSLA.png", "roi": 1.2},
    },
    {
        "MSFT": {"price": 10, "image": "/static/turn10/MSFT.png", "roi": 0.9},
        "AAPL": {"price": 130, "image": "/static/turn10/AAPL.png", "roi": 1.1},
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
    if request.method != "POST":
        return render_template("login.html")
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
        if "game_start_time" not in session:
            session["game_start_time"] = datetime.now().timestamp()  # Store game start timestamp

        session["cash"] = user.capital
        return redirect("/trade")

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/trade")
def trade():
    username = session.get("username")
    if not username:
        return redirect("/")
    
    turn = session.get("turn", 0)
    if turn >= len(STOCK_PRICES):
        return jsonify({"message": "Game Over"})
    
    stock_data = STOCK_PRICES[turn]
    user = User.query.filter_by(username=username).first()
    holdings = {holding.ticker: holding.quantity for holding in user.holdings}
    
    # Assign a different headline per turn
    current_headline = HEADLINES[turn]  # Select one headline per turn

    # Get last turn's stock prices
    last_turn_values = {}
    if turn > 0:
        previous_stock_data = STOCK_PRICES[turn - 1]
        for ticker in previous_stock_data:
            last_turn_values[ticker] = holdings.get(ticker, 0) * previous_stock_data[ticker]["price"]
    # Calculate portfolio value
    portfolio_value = sum(
        holdings.get(ticker, 0) * stock_data[ticker]["price"]
        for ticker in stock_data
    )

    print(f"[DEBUG] User: {username}, Turn: {turn + 1}, Holdings: {holdings}, Portfolio Value: {portfolio_value}")
    
    cash = session.get("cash", user.capital)  # Keep track of cash separately
    
    return render_template(
        "trade.html",
        username=username,
        capital=user.capital,
        cash=cash,
        stock_data=stock_data,
        holdings=holdings,
        portfolio_value=portfolio_value,
        headline=current_headline,  # Pass headline to frontend
        last_turn_values=last_turn_values,  # ✅ Pass last turn values
        turn=turn + 1   
    )

@app.route("/action", methods=["POST"])
def action():
    data = request.json  # ✅ Ensure `data` is received properly
    if not data:
        return jsonify({"error": "Invalid request, no data received"}), 400

    username = data.get("username")
    action = data.get("action")
    ticker = data.get("ticker")
    quantity = int(data.get("quantity", 0) or 0)
    game_timer = data.get("game_timer", "00:00")  # ✅ Ensure game timer exists

    if not username or not action or not ticker:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"[ERROR] User '{username}' not found!")  # Debugging log
        return jsonify({"error": "User not found"}), 400  

    capital_before = user.capital

    holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()
    turn = session.get("turn", 0)  # ✅ Ensure 'turn' exists
    stock = STOCK_PRICES[turn].get(ticker, {})
    price = stock.get("price", 100)

    cash = session.get("cash", user.capital)  # ✅ Ensure cash is properly retrieved

    if quantity <= 0:
        return jsonify({"error": "Invalid trade quantity"}), 400
    if quantity > 100000:
        return jsonify({"error": "Trade size too large"}), 400

    if action == "Buy":
        cost = price * quantity
        if cash >= cost:
            cash -= cost
            user.capital -= cost
            if holding:
                holding.quantity += quantity
            else:
                holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=quantity)
                db.session.add(holding)
        else:
            return jsonify({"error": "Insufficient cash"}), 400
    elif action == "Sell":
        if holding and holding.quantity >= quantity:
            cash += price * quantity
            holding.quantity -= quantity
        else:
            return jsonify({"error": "Not enough shares to sell"}), 400

    session["cash"] = cash

    # ✅ Calculate portfolio value
    holdings = {h.ticker: h.quantity for h in user.holdings}
    stock_data = STOCK_PRICES[turn]
    portfolio_value = sum(holdings.get(ticker, 0) * stock_data[ticker]["price"] for ticker in stock_data)

    user.capital = max(0, cash + portfolio_value)  # ✅ Prevent negative capital

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Database commit failed: {e}")  
        return jsonify({"error": "Transaction failed, please try again."}), 500

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ✅ Readable timestamp
    timestamp = f"{current_time} (Turn {turn + 1}: {game_timer})"

    if user:
        with open(LOG_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                timestamp, username, turn + 1, action, ticker, quantity,
                capital_before, user.capital, portfolio_value
            ])

    return jsonify({
        "holdings": holdings,
        "capital": round(user.capital, 2),
        "cash": round(cash, 2),
        "portfolio": round(portfolio_value, 2)
    })

@app.route("/next-turn", methods=["POST"])
def next_turn():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 400

    turn = session.get("turn", 0)
    if turn >= len(STOCK_PRICES) - 1:
        return jsonify({"message": "Game Over"})  # If game has ended

    session["turn"] = session.get("turn", 0) + 1  # Ensure `turn` exists

    stock_data = STOCK_PRICES[session["turn"]]  # Load new stock prices
    holdings = {h.ticker: h.quantity for h in user.holdings}

    portfolio_value = sum(
        holdings.get(ticker, 0) * stock_data[ticker]["price"]
        for ticker in stock_data
    )

    session["cash"] = max(0, session.get("cash", user.capital))  # Keep cash non-negative
    user.capital = session["cash"] + portfolio_value  # Update total capital
    
    db.session.commit()

    return jsonify({
        "message": "Next turn started",
        "turn": session["turn"],
        "capital": round(user.capital, 2),
        "portfolio": round(portfolio_value, 2),
        "cash": round(session.get("cash", 0), 2),
        "holdings": holdings
    })


# Add the remaining function definitions (login, trade, action, etc.)
if __name__ == "__main__":
    app.run(debug=True)