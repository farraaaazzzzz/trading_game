# Trading Game Web App

This project is a web-based trading game designed for our Final Year Project (FYP) in Institute of Business and Administration (IBA). The app allows users to log in, view dynamically updating stock prices, and perform actions such as buying or selling stocks. User actions are logged for analysis, making it an excellent tool for experimental or educational purposes.

---

## **Features**

- **User Authentication**: Users can log in with predefined credentials stored in the database.
- **Dynamic Stock Prices**: Stock prices fluctuate by ±10% every round.
- **Trading Actions**: Users can buy, sell, or hold stocks, which are reflected in their capital.
- **Round Timer**: Each trading round lasts 1 minute and 45 seconds.
- **Action Logging**: All trades are logged in a CSV file for later analysis.
- **Backend Management**: Built with Flask and SQLAlchemy to manage users, stock prices, and trades.

---

## **Technologies Used**

- **Frontend**:
  - HTML, CSS (integrated into templates)
  - JavaScript (for timer, stock selection, and fetch calls)
- **Backend**:
  - Python
  - Flask
  - SQLAlchemy
- **Database**:
  - SQLite
- **Logging**:
  - CSV for user action tracking

---

## **Setup Instructions**

### **1. Clone the Repository**
Clone the project from the shared source:
```bash
git clone <repository-url>
cd trading_game
```

### **2. Install Dependencies**
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### **3. Initialize the Database**
Run the following command to set up the database and populate initial stock prices:
```bash
flask init-db
```

This creates the `users.db` SQLite database with the following tables:
- `User` (for user accounts)
- `StockPrice` (for stock price management)

### **4. Run the Application**
Start the Flask server:
```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000/`.

### **5. Testing the App**
1. Log in using one of the predefined credentials:
   - **Username**: `user1`
   - **Password**: `password1`

2. Start trading by selecting a stock ticker, entering a quantity, and clicking "Buy" or "Sell".

3. Observe the dynamically updating stock prices and capital adjustments.

4. Check the `trading_logs.csv` file for logged user actions.

---

## **Project Structure**

```
trading_game/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── login.html         # Login page
│   ├── trade.html         # Trading interface
├── static/                # Static files (e.g., images, CSS)
├── requirements.txt       # Python dependencies
├── users.db               # SQLite database
├── trading_logs.csv       # CSV file for action logs
├── README.md              # Project documentation
```

---

## **File Explanations**

### **1. app.py**
The backend Flask application:
- Manages routes for login (`/`) and trading (`/trade/<username>`).
- Handles stock price updates and user actions (`/action`).
- Logs user actions in a CSV file.
- Defines database models (`User`, `StockPrice`).

### **2. templates/**
Contains HTML templates for the frontend:
- **login.html**: User login page.
- **trade.html**: Main trading interface with dynamic prices and timer.

### **3. static/**
Directory for static assets such as images, JavaScript, and CSS.

### **4. users.db**
SQLite database file to store:
- User credentials and capital.
- Stock prices.

### **5. trading_logs.csv**
CSV file that logs each user action:
- `username`, `timestamp`, `action`, `ticker`, `quantity`, `capital_before`, `capital_after`.

### **6. requirements.txt**
Contains all Python dependencies for the project:
```
Flask
Flask-SQLAlchemy
```

---

## **Potential Enhancements**

- **Secure Password Storage**: Use password hashing (e.g., `bcrypt`) instead of plain text.
- **Enhanced Logging**: Include more details like round number or session duration.
- **Deployment**: Deploy the app to a hosting service like Render, Deta Space, or PythonAnywhere.
- **UI Improvements**: Add Bootstrap or similar frameworks for a better user interface.

---

## **Contributors**
- **You**: Faraz Shaikh
- **Partner**: Hassan Naeem

---

For any questions or support, please contact m.shaikh.23114@khi.iba.edu.pk.
