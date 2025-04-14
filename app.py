from flask import Flask, render_template, request, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
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
    capital = db.Column(db.Float, default=10000.0)

# User holdings model
class UserHoldings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref=db.backref('holdings', lazy=True))

HEADLINES = [
    "'Elon Musk's $5 Billion Tesla Stock Sale Raises Eyebrows.'\n\n\n'ExxonMobil Announces Final Investment Decision (FID) for Mega China Petchem Project.'\n\n\n",
    "'Netflix Faces Surge in Phishing Attacks: Over 50% of Users were Targeted.'\n\n\n'P&G's Acquisition of Farmacy Beauty Strengthens Skincare Portfolio and Appeals to Younger Consumers.'\n\n",
    "'ExxonMobil's $25 Billion Annual Investment Plan Through Next 5 years Sparks Investor Optimism Amid Rising Oil Prices.'\n\n'Netflix Dominates Streaming Market with Over 210 Million Subscribers, Outpacing Disney+ by More Than 100 Million.'\n\n",
    "'Tesla Faked Original Full Self-Driving Video, Former Employees Allege.'\n\n\n'Procter & Gamble is unlikely to repeat its stellar performance of recent years, however, it is an excellent wealth preservation vehicle.'\n\n",
    "'Hyundai Ioniq 5 Emerges as Strong Competitor, Posing Threat to Tesla's Market Share in EV Segment.'\n\n'Netflix Planning to change their No-Ad Strategy Amid Slowing Subscriber Growth, Analyst Warns.'\n\n",
    "'Sell All the Shares of the Stocks you Own.'\n\n\n\n\n\n",
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
    {
        "TSLA": {"price": 362.71, "image": "/static/turn5/TSLA.png", "roi": 1},
        "XOM": {"price": 66.75, "image": "/static/turn5/XOM.png", "roi": 1},
        "NFLX": {"price": 567.52, "image": "/static/turn5/NFLX.png", "roi": 1},
        "PG": {"price": 164.21, "image": "/static/turn5/PG.png", "roi": 1},
    },
]

# Initialize CSV for trade logs
LOG_FILE = "trading_log.csv"
TICKERS = ["TSLA", "XOM", "NFLX", "PG"]  # Add all ticker symbols here
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "username", "turn", "action", "ticker", "quantity","capital_before", "capital_after",
            "cash_before", "cash_after",  # ✅ New cash tracking
            "portfolio_before", "portfolio_after", "Total_assets"  # ✅ New portfolio tracking
        ] + [f"total_{ticker}_holding" for ticker in TICKERS] + [f"{ticker}_value" for ticker in TICKERS]
        )
@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
        # Add multiple users with predefined usernames and passwords
        users = [
            {"username": "N0801", "password": "N0801"},
            {"username": "N5202", "password": "N5202"},
            {"username": "N8203", "password": "N8203"},
            {"username": "N5804", "password": "N5804"},
            {"username": "N8905", "password": "N8905"},
            {"username": "N4606", "password": "N4606"},
            {"username": "N0307", "password": "N0307"},
            {"username": "N2408", "password": "N2408"},
            {"username": "N4909", "password": "N4909"},
            {"username": "N6910", "password": "N6910"},
            {"username": "N6211", "password": "N6211"},
            {"username": "N7312", "password": "N7312"},
            {"username": "N8713", "password": "N8713"},
            {"username": "N2314", "password": "N2314"},
            {"username": "N2915", "password": "N2915"},
            {"username": "N3916", "password": "N3916"},
            {"username": "N6717", "password": "N6717"},
            {"username": "N1818", "password": "N1818"},
            {"username": "N9319", "password": "N9319"},
            {"username": "N3220", "password": "N3220"},
            {"username": "N2721", "password": "N2721"},
            {"username": "N0222", "password": "N0222"},
            {"username": "N0523", "password": "N0523"},
            {"username": "N9424", "password": "N9424"},
            {"username": "N0925", "password": "N0925"},
            {"username": "N8626", "password": "N8626"},
            {"username": "N6027", "password": "N6027"},
            {"username": "N9228", "password": "N9228"},
            {"username": "N1029", "password": "N1029"},
            {"username": "N7030", "password": "N7030"},
            {"username": "N0031", "password": "N0031"},
            {"username": "N0132", "password": "N0132"},
            {"username": "N0433", "password": "N0433"},
            {"username": "N0634", "password": "N0634"},
            {"username": "N0735", "password": "N0735"},
            {"username": "N1136", "password": "N1136"},
            {"username": "N1237", "password": "N1237"},
            {"username": "N1338", "password": "N1338"},
            {"username": "N1439", "password": "N1439"},
            {"username": "N1540", "password": "N1540"},
            {"username": "N1641", "password": "N1641"},
            {"username": "N1742", "password": "N1742"},
            {"username": "N1943", "password": "N1943"},
            {"username": "N2044", "password": "N2044"},
            {"username": "N2145", "password": "N2145"},
            {"username": "N2246", "password": "N2246"},
            {"username": "N2547", "password": "N2547"},
            {"username": "N2648", "password": "N2648"},
            {"username": "N2849", "password": "N2849"},
            {"username": "N3050", "password": "N3050"},
            {"username": "N3151", "password": "N3151"},
            {"username": "N3352", "password": "N3352"},
            {"username": "N3453", "password": "N3453"},
            {"username": "N3554", "password": "N3554"},
            {"username": "N3655", "password": "N3655"},
            {"username": "N3756", "password": "N3756"},
            {"username": "N3857", "password": "N3857"},
            {"username": "N4058", "password": "N4058"},
            {"username": "N4159", "password": "N4159"},
            {"username": "N4260", "password": "N4260"},
            {"username": "N4361", "password": "N4361"},
            {"username": "N4462", "password": "N4462"},
            {"username": "N4563", "password": "N4563"},
            {"username": "N4764", "password": "N4764"},
            {"username": "N4865", "password": "N4865"},
            {"username": "N5066", "password": "N5066"},
            {"username": "N5167", "password": "N5167"},
            {"username": "N5368", "password": "N5368"},
            {"username": "N5469", "password": "N5469"},
            {"username": "N5570", "password": "N5570"},
            
            {"username": "E1301", "password": "E1301"},
            {"username": "E5002", "password": "E5002"},
            {"username": "E6403", "password": "E6403"},
            {"username": "E3704", "password": "E3704"},
            {"username": "E5105", "password": "E5105"},
            {"username": "E7206", "password": "E7206"},
            {"username": "E3007", "password": "E3007"},
            {"username": "E3508", "password": "E3508"},
            {"username": "E8509", "password": "E8509"},
            {"username": "E2010", "password": "E2010"},
            {"username": "E4011", "password": "E4011"},
            {"username": "E0712", "password": "E0712"},
            {"username": "E6113", "password": "E6113"},
            {"username": "E2514", "password": "E2514"},
            {"username": "E5515", "password": "E5515"},
            {"username": "E6516", "password": "E6516"},
            {"username": "E1217", "password": "E1217"},
            {"username": "E1518", "password": "E1518"},
            {"username": "E1719", "password": "E1719"},
            {"username": "E6820", "password": "E6820"},
            {"username": "E5721", "password": "E5721"},
            {"username": "E8122", "password": "E8122"},
            {"username": "E7123", "password": "E7123"},
            {"username": "E4524", "password": "E4524"},
            {"username": "E4225", "password": "E4225"},
            {"username": "E0426", "password": "E0426"},
            {"username": "E9127", "password": "E9127"},
            {"username": "E8328", "password": "E8328"},
            {"username": "E7729", "password": "E7729"},
            {"username": "E1130", "password": "E1130"},
            {"username": "E9931", "password": "E9931"},
            {"username": "E9832", "password": "E9832"},
            {"username": "E9733", "password": "E9733"},
            {"username": "E9634", "password": "E9634"},
            {"username": "E9535", "password": "E9535"},
            {"username": "E9036", "password": "E9036"},
            {"username": "E8837", "password": "E8837"},
            {"username": "E8438", "password": "E8438"},
            {"username": "E8039", "password": "E8039"},
            {"username": "E7940", "password": "E7940"},
            {"username": "E7841", "password": "E7841"},
            {"username": "E7642", "password": "E7642"},
            {"username": "E7543", "password": "E7543"},
            {"username": "E7444", "password": "E7444"},
            {"username": "E6645", "password": "E6645"},
            {"username": "E6346", "password": "E6346"},
            {"username": "E5947", "password": "E5947"},
            {"username": "E5648", "password": "E5648"},
            {"username": "E5449", "password": "E5449"},
            {"username": "E5350", "password": "E5350"},
            {"username": "E4851", "password": "E4851"},
            {"username": "E4752", "password": "E4752"},
            {"username": "E4453", "password": "E4453"},
            {"username": "E4354", "password": "E4354"},
            {"username": "E4155", "password": "E4155"},
            {"username": "E3856", "password": "E3856"},
            {"username": "E3657", "password": "E3657"},
            {"username": "E3458", "password": "E3458"},
            {"username": "E3359", "password": "E3359"},
            {"username": "E3160", "password": "E3160"},
            {"username": "E2861", "password": "E2861"},
            {"username": "E2662", "password": "E2662"},
            {"username": "E2263", "password": "E2263"},
            {"username": "E2164", "password": "E2164"},
            {"username": "E1965", "password": "E1965"},
            {"username": "E1666", "password": "E1666"},
            {"username": "E1467", "password": "E1467"},
            {"username": "E0668", "password": "E0668"},
            {"username": "E0169", "password": "E0169"},
            {"username": "E0070", "password": "E0070"}
        ]
        for user_data in users:
            if not User.query.filter_by(username=user_data["username"]).first():
                db.session.add(User(**user_data))
        db.session.commit()
        print("Database initialized with multiple users.")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method != "POST":
        return render_template("login.html")
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()

    if user and user.password == password:
        # Reset user capital
        user.capital = 10000.0
        # Reset user holdings
        existing_holdings = UserHoldings.query.filter_by(user_id=user.id).all()
        for holding in existing_holdings:
            holding.quantity = 0

        db.session.commit()

        # Update CSV header
        with open(LOG_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "timestamp", "username", "turn", "action", "ticker", "quantity","cash_before", "cash_after",  # ✅ New cash tracking
                "stockportfolio_before", "stockportfolio_after", "Total_assets"  # ✅ New portfolio tracking
            ]+ [f"total_{ticker}_holding" for ticker in TICKERS] + [f"{ticker}_value" for ticker in TICKERS])  # Add columns for cumulative holdings

        session["username"] = username
        session["turn"] = 0

        # Ensure user holdings exist for all stocks
        for ticker in TICKERS:
            holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()
            if not holding:
                holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=0)
                db.session.add(holding)

        db.session.commit()  # Save changes to database

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

    # Ensure all tickers exist in holdings dictionary
    for ticker in TICKERS:
        if ticker not in holdings:
            holdings[ticker] = 0

    
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

    holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()
    price = stock_data[ticker]["price"]

    holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()
    if not holding:
        holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=0)
        db.session.add(holding)
        db.session.commit()

    if quantity <= 0:
        return jsonify({"error": "Invalid trade quantity"}), 400
    if quantity > 10000:
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
    user.capital = max(0, cash_after + portfolio_after)
    
    # Calculate total holdings (sum of all stock quantities)
    total_holdings = sum(holdings.values())

    user.capital = max(0, cash_after + portfolio_after)  # ✅ Ensure capital is correct

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Database commit failed: {e}")  
        return jsonify({"error": "Transaction failed, please try again."}), 500

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # ✅ Readable timestamp
    timestamp = f"{current_time} (Turn {turn + 1}: {game_timer})"
    
    # Prepare cumulative holdings data for each ticker
    total_holdings = [holdings.get(ticker, 0) for ticker in TICKERS]
    stock_values = [holdings.get(ticker, 0) * stock_data[ticker]["price"] for ticker in TICKERS]

    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, username, turn + 1, action, ticker, quantity,
            cash_before, cash_after,  # ✅ Cash values before/after
            portfolio_before, portfolio_after,  # ✅ Portfolio before/after
            user.capital,  # ✅ Ensure final capital is logged correctly
        ] + total_holdings + stock_values)  

    return jsonify({
        "holdings": holdings,
        "capital": round(user.capital, 2),
        "cash": round(cash_after, 2),
        "portfolio": round(portfolio_after, 2)
    })
    
# ✅ Ensure an 'exports' directory exists
EXPORTS_DIR = "exports"
LOG_FILE = "trading_log.csv"

def export_user_log(username):
    try:
        df = pd.read_csv(LOG_FILE)

        if df.empty:
            print(f"[WARNING] No trades found for {username}, nothing to export.")
            return

        user_df = df[df["username"] == username]  # ✅ Filter user's trades only

        if user_df.empty:
            print(f"[WARNING] {username} has no trades recorded.")
            return

        # Generate timestamp in the format: DD-MM-HH-MM
        timestamp = datetime.now().strftime('%d-%m-%H-%M')
        user_log_filename = os.path.join(EXPORTS_DIR, f"{username}_{timestamp}_log.csv")

        # Ensure the exports directory exists
        os.makedirs(EXPORTS_DIR, exist_ok=True)

        # Save user log
        user_df.to_csv(user_log_filename, index=False)

        print(f"[LOG EXPORTED] Trading log for {username} saved as {user_log_filename}!")

    except Exception as e:
        print(f"[ERROR] Failed to export trading log for {username}: {e}")


@app.route("/next-turn", methods=["POST"])
def next_turn():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 400

    turn = session.get("turn", 0)
    
    # ✅ If it's the last turn, export logs and prevent further execution
    if turn >= len(STOCK_PRICES) - 1:
        export_user_log(username)  # ✅ Export this user's log
        session.clear()  # ✅ Clear user session to force logout
        return jsonify({"message": "Game Over, logs exported!"})  # ✅ Stop execution after game ends

    # ✅ Store old portfolio & cash BEFORE updating turn
    stock_data_old = STOCK_PRICES[turn]  # Old turn stock prices
    holdings = {h.ticker: h.quantity for h in user.holdings}

    portfolio_before = sum(
        holdings.get(ticker, 0) * stock_data_old[ticker]["price"]
        for ticker in stock_data_old
    )
    cash_before = session.get("cash", user.capital)  # ✅ Ensure cash is stored correctly

    # ✅ Move to the next turn safely
    session["turn"] = turn + 1  

    # ✅ Check if next turn exists to avoid index errors
    if session["turn"] >= len(STOCK_PRICES):
        session["turn"] = len(STOCK_PRICES) - 1  # ✅ Ensure it doesn't go out of bounds

    # ✅ Load new stock prices
    stock_data_new = STOCK_PRICES[session["turn"]]

    # ✅ Calculate new portfolio value based on NEW prices
    portfolio_after = sum(
        holdings.get(ticker, 0) * stock_data_new[ticker]["price"]
        for ticker in stock_data_new
    )

    # ✅ Ensure cash doesn't change during turn transition
    cash_after = cash_before  
    session["cash"] = cash_after  # ✅ Update session cash

    # ✅ Correctly update capital with the **NEW** portfolio value
    capital_before = user.capital  
    user.capital = cash_after + portfolio_after  # ✅ FIXED: Use updated portfolio value

    # ✅ Debugging logs
    print(f"\n[TURN {session['turn']}] ---------------------")
    print(f"   - Cash Before: {cash_before}, Cash After: {cash_after}")
    print(f"   - Portfolio Before: {portfolio_before}, Portfolio After: {portfolio_after}")
    print(f"   - Capital Before: {capital_before}, Capital After: {user.capital}")

    # ✅ Commit to database safely
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Database commit failed: {e}")
        return jsonify({"error": "Database error"}), 500

    return jsonify({
        "message": "Next turn started",
        "turn": session["turn"],
        "capital": round(user.capital, 2),  # ✅ Ensures updated portfolio reflects correctly
        "portfolio": round(portfolio_after, 2),
        "cash": round(cash_after, 2),
        "holdings": holdings
    })

# @app.route("/logout", methods=["POST"])
# def logout():
#     session.clear()  # ✅ Completely clear the user session
#     return jsonify({"message": "Logged out"}), 200
    
def export_log(username):
    """Exports the trading log for a specific user."""
    try:
        source_file = "trading_log.csv"
        destination_file = f"{username}_trading_log.csv"
        shutil.copy(source_file, destination_file)
        print(f"[EXPORT] Trading log saved as {destination_file}")
    except Exception as e:
        print(f"[ERROR] Failed to export log: {e}")

# Add the remaining function definitions (login, trade, action, etc.)
if __name__ == "__main__":
    app.run(debug=True)