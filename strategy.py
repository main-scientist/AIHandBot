from pybit.unified_trading import HTTP
import numpy as np
import pandas as pd
from advanced_ta import LorentzianClassification
import json
import time

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
        
        date = df.tail(1)['date'].dt.strftime('%Y-%m-%d %H:%M:%S').item()
        price_now = pd.to_numeric(df.tail(1)["close"].item())
        signal = pd.to_numeric(df_lc.tail(1)["signal"].item())
        
        if signal == self.pred_position:
            return None
        
        if signal == self.position:
            pos = "hold long" if signal == 1 else "hold short"
        if (signal != self.position) and signal == -1:
            pos = "short"
        if (signal != self.position) and signal == 1:
            pos = "long"
        
        # short
        if signal == -1:
            if self.position == 0:
                self.position = signal
                self.enter_price = price_now
                report = self.get_enter_report(date, pos)
                return report

            # exit from long by signal
            if self.position == 1:
                v = (self.bank / (self.enter_price / self.leverage))
                fee_open = (self.enter_price * v) * self.fee / 100
                fee_close = (price_now * v) * self.fee / 100
                bank = price_now * (self.bank / (self.enter_price / self.leverage)) - self.enter_price * (self.bank / (self.enter_price / self.leverage))  \
                    + self.bank - fee_open - fee_close
                self.enter_price = price_now
                # self.bank = bank
                self.position = signal
                self.pred_position = 1
            
            # exit from long by take profit
            if (((price_now  - self.enter_price) / self.enter_price * 100) > 0.35) and self.pred_position != 1:
                v = (self.bank / (self.enter_price / self.leverage))
                fee_open = (self.enter_price * v) * self.fee / 100
                fee_close = (price_now * v) * self.fee / 100
                bank = price_now * (self.bank / (self.enter_price / self.leverage)) - self.enter_price * (self.bank / (self.enter_price / self.leverage))  \
                    + self.bank - fee_open - fee_close
                # self.bank = bank
                self.position = 0
                self.pred_position = 1
        
        # long    
        if signal == 1:
            if self.position == 0:
                self.position = signal
                self.enter_price = price_now
                report = self.get_enter_report(date, pos)
                return report
                
            # exit from short by signal
            if self.position == -1:
                if ((self.enter_price  - price_now) / price_now * 100) > 0.35:
                    v = (self.bank / (self.enter_price / self.leverage))
                    fee_open = (self.enter_price * v) * self.fee / 100
                    fee_close = (price_now * v) * self.fee / 100
                    bank = self.enter_price * (self.bank / (self.enter_price / self.leverage)) - price_now * (self.bank / (self.enter_price / self.leverage)) \
                        + self.bank - fee_open - fee_close
                    self.enter_price = price_now
                    # self.bank = bank
                    self.position = signal
                    self.pred_position = -1
                    
            # exit form short by take profit
            if (((self.enter_price - price_now) / price_now * 100) > 0.35) and self.pred_position != -1:
                v = (self.bank / (self.enter_price / self.leverage))
                fee_open = (self.enter_price * v) * self.fee / 100
                fee_close = (price_now * v) * self.fee / 100
                bank = self.enter_price * (self.bank / (self.enter_price / self.leverage)) - price_now * (self.bank / (self.enter_price / self.leverage)) \
                        + self.bank - fee_open - fee_close
                # self.bank = bank
                self.position = 0
                self.pred_position = -1
                
        if self.bank == bank:
            return None
        
        report = self.get_report(date, price_now, pos, bank)
        self.bank = bank
            
        return report
    
    
    def get_enter_report(self, date, pos):
        report = {
            "token": self.TOKEN,
            "bank": self.bank,
            "date": date,
            "enter_price": self.enter_price,
            "pos": pos
        }
        return report
    
    def get_report(self, date, price_now, pos, new_bank):
        report = {
            "token": self.TOKEN,
            "date": date,
            "enter_price": self.enter_price,
            "exit_price": price_now,
            "old_bank": self.bank,
            "new_bank": new_bank,
            "percent": ((new_bank - self.bank) / self.bank * 100),
            "pred_position": self.pred_position,
            "new_position": pos,
        }
        return report
        
    
    def get_data_from_bybit(self):
        flag = True
        while flag:   
            try:
                session = HTTP()
                a = session.get_kline(
                    category="linear",
                    symbol=self.TOKEN,
                    interval=self.timeline,
                    # start=start_timestamp,
                    # end=end_timestamp,
                    limit=1000
                )
                flag = False
            except Exception as e:
                print("Error pybit")
            time.sleep(1)
            
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
    
    
    # def exit_from_position(self):
    #     df, df_lc  = self.get_data_from_bybit()
        
    #     self.date = df.tail(1)['date'].dt.strftime('%Y-%m-%d %H:%M:%S').item()
    #     enter_price = self.enter_price
    #     price_now = pd.to_numeric(df.tail(1)["close"].item())
        
    #     # exit from long
    #     if self.position == 1:
    #         v = (self.bank / (self.enter_price / self.leverage))
    #         fee_open = (self.enter_price * v) * self.fee / 100
    #         fee_close = (price_now * v) * self.fee / 100
    #         bank = price_now * (self.bank / (self.enter_price / self.leverage)) - self.enter_price * (self.bank / (self.enter_price / self.leverage))  \
    #             + self.bank - fee_open - fee_close
    #         self.enter_price = 0
    #         self.bank = bank
    #         self.position = 0
    #         self.pred_position = 1
            
    #      # exit from short
    #     if self.position == -1:
    #         v = (self.bank / (self.enter_price / self.leverage))
    #         fee_open = (self.enter_price * v) * self.fee / 100
    #         fee_close = (price_now * v) * self.fee / 100
    #         bank = self.enter_price * (self.bank / (self.enter_price / self.leverage)) - price_now * (self.bank / (self.enter_price / self.leverage)) \
    #             + self.bank - fee_open - fee_close
    #         self.enter_price = 0
    #         self.bank = bank
    #         self.position = 0
    #         self.pred_position = -1
            
    #     return enter_price, price_now
    
    
    def get_rate_now(self):
        try:
            session = HTTP()
            a = session.get_kline(
                category="linear",
                symbol=self.TOKEN,
                interval=self.timeline,
                limit=1
            )
        except Exception as e:
            return "Custom except: error load data from api bybit", "Error"
        columns = ["date", "open", "high", "low", "close"]
        
        timestamps_milliseconds = [item[0] for item in a["result"]["list"]]
        timestamps_numeric = pd.to_numeric(timestamps_milliseconds)
        df = pd.DataFrame({
            "date": pd.to_datetime(timestamps_numeric, unit='ms', origin='unix'),
            "open": [item[1] for item in a["result"]["list"]],
            "high": [item[2] for item in a["result"]["list"]],
            "low": [item[3] for item in a["result"]["list"]],
            "close": [item[4] for item in a["result"]["list"]],
            "volume": [item[5] for item in a["result"]["list"]],
        })
        columns = ["date", "open", "high", "low", "close"]
        df = df[columns]
        df = pd.DataFrame(df, columns=columns)
        df = df.sort_index(ascending=False)
        df = df.reset_index()
        df = df.drop(["index"], axis=1)
        df["open"] = pd.to_numeric(df["open"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["close"] = pd.to_numeric(df["close"])
        
        return df["close"].item()