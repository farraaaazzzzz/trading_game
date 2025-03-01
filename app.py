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
    "Elon Musk's $5 Billion Tesla Stock Sale Raises Eyebrows.\nExxonMobil Announces FID for Mega China Petchem Project.\n.\n.",
    "Netflix Faces Surge in Phishing Attacks: Over 50% of Users were Targeted.\nP&G's Acquisition of Farmacy Beauty Strengthens Skincare Portfolio and Appeals to Younger Consumers.",
    "ExxonMobil's $25 Billion Annual Investment Plan Through Next 5 years Sparks Investor Optimism Amid Rising Oil Prices.\nNetflix Dominates Streaming Market with Over 210 Million Subscribers, Outpacing Disney+ by More Than 100 Million.",
    "Tesla Faked Original Full Self-Driving Video, Former Employees Allege.\nProcter & Gamble is unlikely to repeat its stellar performance of recent years, however, it is an excellent wealth preservation vehicle.",
    "Hyundai Ioniq 5 Emerges as Strong Competitor, Posing Threat to Tesla's Market Share in EV Segment.\nNetflix Planning to change their No-Ad Strategy Amid Slowing Subscriber Growth, Analyst Warns.",
]

# Game configuration: Fixed stock prices & hidden ROI percentages
STOCK_PRICES = [
    {
        "TSLA": {"price": 337.8, "image": "/static/turn1/TSLA.png", "roi": 1.101243339},
        "XOM": {"price": 64.37, "image": "/static/turn1/XOM.png", "roi": 0.986173683},
        "NFLX": {"price": 679.33, "image": "/static/turn1/NFLX.png", "roi": 0.969028307},
        "PG": {"price": 147.4, "image": "/static/turn1/PG.png", "roi": 1.008548168},
    },
    {
        "TSLA": {"price": 372, "image": "/static/turn2/TSLA.png", "roi": 0.904139785},
        "XOM": {"price": 63.48, "image": "/static/turn2/XOM.png", "roi": 0.970069313},
        "NFLX": {"price": 658.29, "image": "/static/turn2/NFLX.png", "roi": 0.930729618},
        "PG": {"price": 148.66, "image": "/static/turn2/PG.png", "roi": 1.023476389},
    },
    {
        "TSLA": {"price": 336.34, "image": "/static/turn3/TSLA.png", "roi": 0.967265267},
        "XOM": {"price": 61.58, "image": "/static/turn3/XOM.png", "roi": 0.994965898},
        "NFLX": {"price": 612.69, "image": "/static/turn3/NFLX.png", "roi": 0.987514077},
        "PG": {"price": 152.15, "image": "/static/turn3/PG.png", "roi": 1.044101216},
    },
    {
        "TSLA": {"price": 325.33, "image": "/static/turn4/TSLA.png", "roi": 1.120861894},
        "XOM": {"price": 61.27, "image": "/static/turn4/XOM.png", "roi": 1.010119145},
        "NFLX": {"price": 605.04, "image": "/static/turn4/NFLX.png", "roi": 1.013354489},
        "PG": {"price": 158.86, "image": "/static/turn4/PG.png", "roi": 1.019576986},
    },
    {
        "TSLA": {"price": 364.65, "image": "/static/turn5/TSLA.png", "roi": 0.99467983},
        "XOM": {"price": 61.89, "image": "/static/turn5/XOM.png", "roi": 1.078526418},
        "NFLX": {"price": 613.12, "image": "/static/turn5/NFLX.png", "roi": 0.925626305},
        "PG": {"price": 161.97, "image": "/static/turn5/PG.png", "roi": 1.013829722},
    },
]

# Initialize CSV for trade logs
LOG_FILE = "trading_log.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "username", "turn", "action", "ticker", "quantity","capital_before", "capital_after",
            "cash_before", "cash_after",  # ✅ New cash tracking
            "portfolio_before", "portfolio_after"  # ✅ New portfolio tracking
        ])
        
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
        return jsonify({"message": "Game Over"}), 400
    
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

    turn = session.get("turn", 0)
    cash_before = session.get("cash", user.capital)  # ✅ Store cash before trade
    stock_data = STOCK_PRICES[turn]  # ✅ Ensure stock data is correctly loaded

    # ✅ Store portfolio before the trade
    holdings = {h.ticker: h.quantity for h in user.holdings}  
    portfolio_before = sum(holdings.get(t, 0) * stock_data[t]["price"] for t in stock_data)

    price = stock_data[ticker]["price"]

    holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()
    if not holding:
        holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=0)
        db.session.add(holding)
        db.session.commit()

    if quantity <= 0:
        return jsonify({"error": "Invalid trade quantity"}), 400
    if quantity > 100000:
        return jsonify({"error": "Trade size too large"}), 400

    if action == "Buy":
        cost = price * quantity
        if cash_before >= cost:
            session["cash"] -= cost  # ✅ Deduct cash **before** updating holdings
            user.capital -= cost

            if holding:
                holding.quantity += quantity  # ✅ Ensure stock quantity updates
            else:
                holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=quantity)
                db.session.add(holding)
            
            db.session.commit()  # ✅ Commit immediately after trade
        else:
            return jsonify({"error": "Insufficient cash"}), 400
        
    elif action == "Sell":
        if holding and holding.quantity >= quantity:
            session["cash"] += price * quantity  # ✅ Add cash **before** updating holdings
            holding.quantity -= quantity
            
            db.session.commit()  # ✅ Commit immediately after trade
        else:
            return jsonify({"error": "Not enough shares to sell"}), 400

    cash_after = session["cash"]  # ✅ Ensure cash update persists

    # ✅ Re-fetch holdings AFTER commit
    holdings = {h.ticker: h.quantity for h in user.holdings}  
    portfolio_after = sum(holdings.get(t, 0) * stock_data[t]["price"] for t in stock_data)

    user.capital = max(0, cash_after + portfolio_after)  # ✅ Ensure capital is correct

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Database commit failed: {e}")  
        return jsonify({"error": "Transaction failed, please try again."}), 500

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ✅ Readable timestamp
    timestamp = f"{current_time} (Turn {turn + 1}: {game_timer})"

    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, username, turn + 1, action, ticker, quantity,
            cash_before, cash_after,  # ✅ Cash values before/after
            portfolio_before, portfolio_after,  # ✅ Portfolio before/after
            user.capital  # ✅ Ensure final capital is logged correctly
        ])

    return jsonify({
        "holdings": holdings,
        "capital": round(user.capital, 2),
        "cash": round(cash_after, 2),
        "portfolio": round(portfolio_after, 2)
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
    
    # ✅ Ensure we don't go beyond available turns
    if turn >= len(STOCK_PRICES) - 1:
        return jsonify({"message": "Game Over"})

    # ✅ Store old portfolio & cash BEFORE updating turn
    stock_data_old = STOCK_PRICES[turn]  # Old turn stock prices
    holdings = {h.ticker: h.quantity for h in user.holdings}

    portfolio_before = sum(
        holdings.get(ticker, 0) * stock_data_old[ticker]["price"]
        for ticker in stock_data_old
    )
    cash_before = session.get("cash", user.capital)  # ✅ Store cash correctly before turn change

    # ✅ Move to the next turn
    session["turn"] = turn + 1  

    # ✅ Load new stock prices
    stock_data_new = STOCK_PRICES[session["turn"]]  # New turn stock prices

    # ✅ Calculate new portfolio value based on NEW prices
    portfolio_after = sum(
        holdings.get(ticker, 0) * stock_data_new[ticker]["price"]
        for ticker in stock_data_new
    )

    # ✅ Cash should NOT change unless a trade happens
    cash_after = cash_before  

    # ✅ Correctly update capital with the **NEW** portfolio value
    capital_before = user.capital  
    user.capital = cash_after + portfolio_after  # ✅ FIXED: Use updated portfolio value

    # ✅ Debugging logs
    print(f"\n[TURN {session['turn']}] ---------------------")
    print(f"   - Cash Before: {cash_before}, Cash After: {cash_after}")
    print(f"   - Portfolio Before: {portfolio_before}, Portfolio After: {portfolio_after}")
    print(f"   - Capital Before: {capital_before}, Capital After: {user.capital}")

    # ✅ Commit to database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Database commit failed: {e}")
        return jsonify({"error": "Database error"}), 500

    return jsonify({
        "message": "Next turn started",
        "turn": session["turn"],
        "capital": round(user.capital, 2),  # ✅ Now correctly reflects new portfolio
        "portfolio": round(portfolio_after, 2),
        "cash": round(cash_after, 2),
        "holdings": holdings
    })

# Add the remaining function definitions (login, trade, action, etc.)
if __name__ == "__main__":
    app.run(debug=True)