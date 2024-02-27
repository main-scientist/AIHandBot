import schedule
import time
import telebot
from telebot import types
from datetime import datetime
import pytz
from functools import partial
from strategy import Strategy
import json
import numpy as np

chat_id_ivan = "568629044"
chat_id_nikita = "341437095"
bot = telebot.TeleBot("6742853817:AAH4bj8AEi2wdHZjpbm-kUbHbddyI4Qnspw")

strategy_sol = Strategy(TOKEN="SOLUSDT", timeline=15, bank=100, leverage=2, fee=0.055, position=0)
strategy_btc = Strategy(TOKEN="BTCUSDT", timeline=15, bank=100, leverage=2, fee=0.055, position=0)
strategy_eth = Strategy(TOKEN="ETHUSDT", timeline=15, bank=100, leverage=2, fee=0.055, position=0)
bot_flag = True

def wrapper_send_message(chat_id, text, time_sleep):
    flag = False
    if not flag:
        try:
            bot.send_message(chat_id, text)
            flag = True
            time.sleep(time_sleep)
        except Exception as e:
            print("Error from telegram")
            time.sleep(1)
        

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Start bot')
    
    global strategy_sol, strategy_btc, strategy_eth, bot_flag
    
    # date_sol = 0
    # date_btc = 0
    
    while bot_flag:
        report_btc = strategy_btc.strategy()
        report_sol = strategy_sol.strategy()
        report_eth = strategy_eth.strategy()
        
        if report_sol is not None:
            wrapper_send_message(chat_id_ivan, json.dumps(report_sol, indent=2, separators=(',', ': ')), 0)
        
        if report_btc is not None:
            wrapper_send_message(chat_id_ivan, json.dumps(report_btc, indent=2, separators=(',', ': ')), 0)
            
        if report_eth is not None:
            wrapper_send_message(chat_id_ivan, json.dumps(report_eth, indent=2, separators=(',', ': ')), 0)
                
        time.sleep(2)

        
@bot.message_handler(commands=['button'])
def button_message(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("exchange rate now")
    item2=types.KeyboardButton("stop the bot")
    item3=types.KeyboardButton("balance")
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    bot.send_message(chat_id_ivan, text="choise action:", reply_markup=markup)
 

@bot.message_handler(content_types='text')
def message_reply(message):
    global strategy_sol, strategy_btc, strategy_eth, bot_flag
    
    if message.text=="exchange rate now":
        
        rate_now_sol, un_profit_sol = strategy_sol.get_rate_now()
        rate_now_btc, un_profit_btc = strategy_btc.get_rate_now()
        rate_now_eth, un_profit_eth = strategy_eth.get_rate_now()
        content = {
            "bank_sol": rate_now_sol,
            "un_profit_sol": un_profit_sol,
            "bank_btc": rate_now_btc,
            "un_profit_btc": un_profit_btc,
            "bank_eth": rate_now_eth,
            "un_profit_eth": un_profit_eth,
        }
        content = json.dumps(content, indent=2, separators=(',', ': '))
        
        wrapper_send_message(chat_id_ivan, content, 0)
    
    if message.text=="stop the bot":
        bot_flag = False
        content = "bot was stopped"
        wrapper_send_message(chat_id_ivan, content, 0)
    
    if message.text=="balance":
        content = {
            "bank_sol": round(strategy_sol.bank, 3),
            "bank_btc": round(strategy_btc.bank, 3),
            "bank_eth": round(strategy_eth.bank, 3)
        }
        content = json.dumps(content, indent=2, separators=(',', ': '))
        wrapper_send_message(chat_id_ivan, content, 0)
    
    # if message.text=="exit from SOl":
    #     try:
    #         enter_price, price_now = strategy_sol.exit_from_position()
    #     except Exception as e:
    #         print("Error from bybit")
    #         time.sleep(1)
    #     content = f"Exited from SOL \n enter_price: {round(enter_price, 2)} \n exit_price: {round(price_now, 2)} \n bank: {round(strategy_sol.bank, 2)} \n pred_position: {strategy_sol.pred_position}"
    #     wrapper_send_message(chat_id_ivan, content, 0)

    # if message.text=="exit from BTC":
    #     try:
    #         enter_price, price_now = strategy_btc.exit_from_position()
    #     except Exception as e:
    #         print("Error from bybit")
    #         time.sleep(1)
    #     content = f"Exited from BTC \n enter_price: {round(enter_price, 2)} \n exit_price: {round(price_now, 2)} \n bank: {round(strategy_btc.bank, 2)} \n pred_position: {strategy_btc.pred_position}"
    #     wrapper_send_message(chat_id_ivan, content, 0)

 
 
 
 
bot.infinity_polling()
