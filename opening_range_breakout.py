import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date
import smtplib, ssl

connection = sqlite3.connect(config.DB_File)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()

cursor.execute("""
               select id from strategy where name = 'opening_range_breakout'
""")

strategy_id = cursor.fetchone()['id']

cursor.execute(
    """
   select symbol, name
   from stock
   join stock_strategy on stock_strategy.stock_id = stock.id
   where stock_strategy.strategy_id = ?
   """, (strategy_id,))

stocks = cursor.fetchall()
symbols = [stock['symbol'] for stock in stocks]

current_date = '2020-10-29'
# current_date = date.today().isoformat()
start_minute_bar = f"{current_date} 09:30:00-04:00"
end_minute_bar = f"{current_date} 09:45:00-04:00"

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)

orders = api.list_orders()
# orders = api.list_orders(status='all', limit=500, after=f"{current_date}T13:30:00Z")
existing_orders_symbols = [order.symbol for order in orders]
# print(existing_orders_symbols)




messages = []
for symbol in symbols:
    
    minute_bars = api.polygon.historic_agg_v2(
        symbol, 1, 'minute', _from=current_date, to=current_date).df

    opening_range_mask = (minute_bars.index >= start_minute_bar) & (
        minute_bars.index < end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]


    opening_range_low = opening_range_bars['low'].min()
    opening_range_high = opening_range_bars['high'].max()
    opening_range = opening_range_high - opening_range_low

    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]

    after_opening_range_breakout = after_opening_range_bars[
        after_opening_range_bars['close'] > opening_range_high]
    if not after_opening_range_breakout.empty:
        if symbol not in existing_orders_symbols:
            # print(after_opening_range_breakout)
            limit_price = after_opening_range_breakout.iloc[0]['close']
            # print(limit_price)

            messages.append(f"Placing order for {symbol}, closed above {opening_range_high} \n\n {after_opening_range_breakout.iloc[0]}\n\n")
            print(f"Placing order for {symbol}, closed above {opening_range_high} at {after_opening_range_breakout.iloc[0]}")

        #     api.submit_order(
        #         symbol=symbol,
        #         side='buy',
        #         type='limit',
        #         qty='100',
        #         time_in_force='day',
        #         order_class='bracket',
        #         limit_price=limit_price,
        #         take_profit=dict(
        #             limit_price=limit_price+opening_range,
        #         ),
        #         stop_loss=dict(
        #             stop_price=limit_price-opening_range,
        #         )
        #     )
        # else:
        #    print(f"Already an order for {symbol}, skipping")
        
print(messages)


context = ssl.create_default_context()
with smtplib.SMTP_SSL(config.EMAIL_HOST,config.EMAIL_PORT, context=context) as server:
    server.login(config.EMAIL_SENDER_ADDRESS, config.EMAIL_PASSWORD)
    
    email_message = f"Subject: Trade Notifications for {current_date}\n\n"
    email_message += "\n\n".join(messages)
    
    server.sendmail(config.EMAIL_SENDER_ADDRESS, config.EMAIL_RECEIVER_ADDRESS, email_message)
    print("Email sent succesfully")
    
    server.sendmail(config.EMAIL_SENDER_ADDRESS, config.EMAIL_SMS, email_message)
    print("SMS notification sent succesfully")
