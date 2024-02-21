from pybit.unified_trading import HTTP
import numpy as np
import pandas as pd
from advanced_ta import LorentzianClassification
import json

class Strategy():
    def __init__(self, TOKEN, timeline, bank, leverage, fee, position):
        self.timeline = timeline
        self.bank = bank
        self.date = 0
        self.leverage = leverage
        self.fee = fee
        self.position, self.pred_position = position, 0
        self.enter_price, self.exit_price = 0, 0
        self.TOKEN = TOKEN
        
    def strategy(self):
        df, df_lc  = self.get_data_from_bybit()
        
        if isinstance(df, str):
            return df, False, False
        
        _date = df.tail(1)['date'].dt.strftime('%Y-%m-%d %H:%M:%S').item()
        price_now = pd.to_numeric(df.tail(1)["close"].item())
        signal = pd.to_numeric(df_lc.tail(1)["signal"].item())
        
        if signal == self.pred_position:
            return df, _date, True
        
        if signal == self.position:
            pos = "hold long" if signal == 1 else "hold short"
        if (signal != self.position) and signal == -1:
            pos = "short"
        if (signal != self.position) and signal == 1:
            pos = "long"
        
        # short
        if signal == -1:
            if self.position == 0:
                self.position = -1
                self.enter_price = price_now
        
            # exit from long
            if self.position == 1:
                v = (self.bank / (self.enter_price / self.leverage))
                fee_open = (self.enter_price * v) * self.fee / 100
                fee_close = (price_now * v) * self.fee / 100
                bank = price_now * (self.bank / (self.enter_price / self.leverage)) - self.enter_price * (self.bank / (self.enter_price / self.leverage))  \
                    + self.bank - fee_open - fee_close
                self.enter_price = price_now
                self.bank = bank
        
        # long    
        if signal == 1:
            if self.position == 0:
                self.position = 1
                self.enter_price = price_now
                
            # exit from short
            if self.position == -1:
                v = (self.bank / (self.enter_price / self.leverage))
                fee_open = (self.enter_price * v) * self.fee / 100
                fee_close = (price_now * v) * self.fee / 100
                bank = self.enter_price * (self.bank / (self.enter_price / self.leverage)) - price_now * (self.bank / (self.enter_price / self.leverage)) \
                    + self.bank - fee_open - fee_close
                self.enter_price = price_now
                self.bank = bank
        
        self.position = signal
        
        report = self.get_report(_date, self.enter_price, price_now, pos, signal)
        return report, _date, False
    
    
    def get_report(self, _date, enter_price, price_now, pos, signal):
        bank = 0
        if signal == -1:
            v = (self.bank / (self.enter_price / self.leverage))
            fee_open = (self.enter_price * v) * self.fee / 100
            fee_close = (price_now * v) * self.fee / 100
            bank = self.enter_price * (self.bank / (self.enter_price / self.leverage)) - price_now * (self.bank / (self.enter_price / self.leverage)) \
                    + self.bank - fee_open - fee_close
                    
        if signal == 1:
            v = (self.bank / (self.enter_price / self.leverage))
            fee_open = (self.enter_price * v) * self.fee / 100
            fee_close = (price_now * v) * self.fee / 100
            bank = price_now * (self.bank / (self.enter_price / self.leverage)) - self.enter_price * (self.bank / (self.enter_price / self.leverage))  \
                + self.bank - fee_open - fee_close
        
        un_profit = round(bank - self.bank, 2)
        un_percent = round(((price_now - enter_price) / enter_price * 100) if signal == 1 else ((enter_price - price_now) / price_now * 100), 2)
        report = {
            "token": self.TOKEN,
            "date": _date,
            "bank": self.bank,
            "position": pos,
            "enter_price": enter_price,
            "price_now": price_now,
            "un_profit": un_profit,
            "un_percent": un_percent
        }
        return report
        
    
    def get_data_from_bybit(self):    
        try:
            session = HTTP()
            a = session.get_kline(
                category="linear",
                symbol=self.TOKEN,
                interval="15",
                # start=start_timestamp,
                # end=end_timestamp,
                limit=1000
            )
        except Exception as e:
            return "Custom except: error load data from api bybit", "Error"
        
        timestamps_milliseconds = [item[0] for item in a["result"]["list"]]
        timestamps_numeric = pd.to_numeric(timestamps_milliseconds)
        df_sol = pd.DataFrame({
            "date": pd.to_datetime(timestamps_numeric, unit='ms', origin='unix'),
            "open": [item[1] for item in a["result"]["list"]],
            "high": [item[2] for item in a["result"]["list"]],
            "low": [item[3] for item in a["result"]["list"]],
            "close": [item[4] for item in a["result"]["list"]],
            "volume": [item[5] for item in a["result"]["list"]],
        })
        
        columns = ["date", "open", "high", "low", "close"]
        df = df_sol[columns]
        df = pd.DataFrame(df, columns=columns)
        df = df.sort_index(ascending=False)
        df = df.reset_index()
        df = df.drop(["index"], axis=1)
        df["open"] = pd.to_numeric(df["open"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["close"] = pd.to_numeric(df["close"])
        
        df_with_out_last = df[:999]
        date = pd.to_datetime(df_with_out_last["date"])
        
        lc = LorentzianClassification(df_with_out_last[["open", "high", "low", "close"]])
        df_lc = lc.data
        df_lc["date"] = date
        
        return df, df_lc
    
    
    def exit_from_position(self):
        df, df_lc  = self.get_data_from_bybit()
        
        self.date = df.tail(1)['date'].dt.strftime('%Y-%m-%d %H:%M:%S').item()
        price_now = pd.to_numeric(df.tail(1)["close"].item())
        
        # exit from long
        if self.position == 1:
            v = (self.bank / (self.enter_price / self.leverage))
            fee_open = (self.enter_price * v) * self.fee / 100
            fee_close = (price_now * v) * self.fee / 100
            bank = price_now * (self.bank / (self.enter_price / self.leverage)) - self.enter_price * (self.bank / (self.enter_price / self.leverage))  \
                + self.bank - fee_open - fee_close
            self.enter_price = 0
            self.bank = bank
            self.position = 0
            self.pred_position = 1
            
         # exit from short
        if self.position == -1:
            v = (self.bank / (self.enter_price / self.leverage))
            fee_open = (self.enter_price * v) * self.fee / 100
            fee_close = (price_now * v) * self.fee / 100
            bank = self.enter_price * (self.bank / (self.enter_price / self.leverage)) - price_now * (self.bank / (self.enter_price / self.leverage)) \
                + self.bank - fee_open - fee_close
            self.enter_price = 0
            self.bank = bank
            self.position = 0
            self.pred_position = -1
            