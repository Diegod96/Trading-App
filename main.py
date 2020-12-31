import sqlite3
import config
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from datetime import date


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    stock_filter = request.query_params.get('filter', False)
    connection = sqlite3.connect(config.DB_File)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    if stock_filter == 'new_closing_highs':
        cursor.execute("""
        SELECT * FROM (
            SELECT symbol, name, stock_id, max(close), date
            FROM stock_price join stock on stock.id = stock_price.stock_id
            GROUP BY stock_id
            ORDER BY symbol
        ) WHERE date = ?
        """, (date.today().isoformat(),))
    else:
        cursor.execute("""
        SELECT id, symbol, name FROM stock ORDER BY symbol
                       """)
        
    rows = cursor.fetchall()

    return templates.TemplateResponse("index.html", {"request": request, "stocks": rows})


@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):

    connection = sqlite3.connect(config.DB_File)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """SELECT id, symbol, name FROM stock WHERE symbol = ?""", (symbol,))
    row = cursor.fetchone()

    cursor.execute(
        """SELECT * FROM stock_price WHERE stock_id = ? ORDER BY date DESC""", (row['id'],))
    prices = cursor.fetchall()

    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": row, "bars": prices})
