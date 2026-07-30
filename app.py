from flask import Flask, render_template, request, redirect, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import pandas as pd
import os
import csv
from datetime import datetime
from flask_migrate import Migrate

import market_data

load_dotenv()

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

# Quick-select chips shown alongside the search box — players can also
# search for (almost) any real, listed ticker via /api/search.
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX", "JPM", "XOM"]

# Per-user trade logs (each user gets their own CSV, so one student's login
# can never truncate or overwrite another student's in-progress trade log)
LOGS_DIR = "logs"
EXPORTS_DIR = "exports"
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_HEADER = [
    "timestamp", "username", "action", "ticker", "quantity", "price",
    "cash_before", "cash_after", "portfolio_before", "portfolio_after", "total_assets",
]

def user_log_path(username):
    return os.path.join(LOGS_DIR, f"{username}_trading_log.csv")

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
        # Reset user capital and holdings — every login starts a fresh game
        user.capital = 10000.0
        existing_holdings = UserHoldings.query.filter_by(user_id=user.id).all()
        for holding in existing_holdings:
            holding.quantity = 0

        db.session.commit()

        # Start a fresh log for this user only (their own file, not shared)
        with open(user_log_path(username), "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(LOG_HEADER)

        session["username"] = username
        session["cash"] = user.capital

        return redirect("/trade")

    return jsonify({"error": "Invalid credentials"}), 401

def holdings_with_value(quantities):
    """Build {ticker: {quantity, price, value}} plus the total portfolio
    value, from a plain {ticker: quantity} dict. A ticker whose quote
    briefly fails is included with price/value=None rather than crashing
    the whole page — it just won't count toward the total until the next
    successful refresh."""
    holdings = {}
    total = 0.0
    for ticker, quantity in quantities.items():
        if quantity <= 0:
            continue
        try:
            price = market_data.get_quote(ticker)
        except market_data.MarketDataError:
            price = None
        value = round(price * quantity, 2) if price is not None else None
        if value is not None:
            total += value
        holdings[ticker] = {"quantity": quantity, "price": price, "value": value}
    return holdings, total

@app.route("/trade")
def trade():
    username = session.get("username")
    if not username:
        return redirect("/")

    user = User.query.filter_by(username=username).first()
    quantities = {h.ticker: h.quantity for h in user.holdings if h.quantity > 0}

    holdings, value = holdings_with_value(quantities)
    cash = session.get("cash", user.capital)
    user.capital = cash + value
    db.session.commit()

    return render_template(
        "trade.html",
        username=username,
        capital=user.capital,
        cash=cash,
        holdings=holdings,
        portfolio_value=value,
        default_tickers=DEFAULT_TICKERS,
    )

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "")
    try:
        return jsonify(market_data.search_symbols(query))
    except market_data.MarketDataError as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/quote/<symbol>")
def api_quote(symbol):
    try:
        return jsonify({"symbol": symbol.upper(), "price": market_data.get_quote(symbol)})
    except market_data.MarketDataError as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/history/<symbol>")
def api_history(symbol):
    try:
        return jsonify({"symbol": symbol.upper(), "history": market_data.get_daily_history(symbol)})
    except market_data.MarketDataError as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/portfolio")
def api_portfolio():
    username = session.get("username")
    if not username:
        return jsonify({"error": "Not logged in"}), 400

    user = User.query.filter_by(username=username).first()
    quantities = {h.ticker: h.quantity for h in user.holdings if h.quantity > 0}
    holdings, value = holdings_with_value(quantities)
    cash = session.get("cash", user.capital)
    user.capital = cash + value
    db.session.commit()

    return jsonify({
        "capital": round(user.capital, 2),
        "cash": round(cash, 2),
        "portfolio": round(value, 2),
        "holdings": holdings,
    })

@app.route("/action", methods=["POST"])
def action():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request, no data received"}), 400

    username = data.get("username")
    trade_action = data.get("action")
    ticker = (data.get("ticker") or "").upper()
    quantity = int(data.get("quantity", 0) or 0)

    if not username or not trade_action or not ticker:
        return jsonify({"error": "Missing required fields"}), 400
    if username != session.get("username"):
        return jsonify({"error": "Not logged in"}), 401
    if quantity <= 0:
        return jsonify({"error": "Invalid trade quantity"}), 400
    if quantity > 10000:
        return jsonify({"error": "Trade size too large"}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 400

    try:
        price = market_data.get_quote(ticker)
    except market_data.MarketDataError as e:
        return jsonify({"error": f"Couldn't get a price for {ticker}: {e}"}), 502

    cash_before = session.get("cash", user.capital)
    quantities_before = {h.ticker: h.quantity for h in user.holdings}
    _, value_before = holdings_with_value(quantities_before)

    holding = UserHoldings.query.filter_by(user_id=user.id, ticker=ticker).first()

    if trade_action == "Buy":
        cost = price * quantity
        if cash_before < cost:
            return jsonify({"error": "Insufficient cash"}), 400
        session["cash"] = cash_before - cost
        if holding:
            holding.quantity += quantity
        else:
            holding = UserHoldings(user_id=user.id, ticker=ticker, quantity=quantity)
            db.session.add(holding)

    elif trade_action == "Sell":
        if not holding or holding.quantity < quantity:
            return jsonify({"error": "Not enough shares to sell"}), 400
        session["cash"] = cash_before + price * quantity
        holding.quantity -= quantity

    else:
        return jsonify({"error": "Unknown action"}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Database commit failed: {e}")
        return jsonify({"error": "Transaction failed, please try again."}), 500

    cash_after = session["cash"]
    quantities_after = {h.ticker: h.quantity for h in user.holdings if h.quantity > 0}
    holdings_after, value_after = holdings_with_value(quantities_after)
    user.capital = max(0, cash_after + value_after)
    db.session.commit()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(user_log_path(username), "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, username, trade_action, ticker, quantity, price,
            cash_before, cash_after, value_before, value_after, user.capital,
        ])

    return jsonify({
        "holdings": holdings_after,
        "capital": round(user.capital, 2),
        "cash": round(cash_after, 2),
        "portfolio": round(value_after, 2),
    })

def export_user_log(username):
    log_path = user_log_path(username)
    try:
        if not os.path.exists(log_path):
            print(f"[WARNING] No trades found for {username}, nothing to export.")
            return

        df = pd.read_csv(log_path)

        if df.empty:
            print(f"[WARNING] {username} has no trades recorded.")
            return

        # Generate timestamp in the format: DD-MM-HH-MM
        timestamp = datetime.now().strftime('%d-%m-%H-%M')
        user_log_filename = os.path.join(EXPORTS_DIR, f"{username}_{timestamp}_log.csv")

        # Ensure the exports directory exists
        os.makedirs(EXPORTS_DIR, exist_ok=True)

        # Save user log
        df.to_csv(user_log_filename, index=False)

        print(f"[LOG EXPORTED] Trading log for {username} saved as {user_log_filename}!")

    except Exception as e:
        print(f"[ERROR] Failed to export trading log for {username}: {e}")

@app.route("/logout", methods=["POST"])
def logout():
    username = session.get("username")
    if username:
        export_user_log(username)
    session.clear()
    return jsonify({"message": "Logged out"}), 200

if __name__ == "__main__":
    app.run(debug=True)
