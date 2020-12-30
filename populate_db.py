import alpaca_trade_api as tradeapi
import sqlite3

connection = sqlite3.connect('app.db')
cursor = connection.cursor()

api = tradeapi.REST('PKE0GX8F12QG3S777QIW', 'X3wymZMeLzUgEkfThIWDjeb7nVofJLN9nXJQSHge', base_url='https://paper-api.alpaca.markets') # or use ENV Vars shown below
assets = api.list_assets()

for asset in assets:
    try:
        if asset.status == 'active' and asset.tradable:
            cursor.execute("INSERT INTO stock (symbol, company) VALUES (?, ?)", (asset.symbol, asset.name))
    except Exception as e:
        print(asset.symbol)
        print(e)


connection.commit()