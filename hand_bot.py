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

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Start bot')
    
    global strategy_sol
    
    while True:
        date = 0
        report_sol, _date_sol, flag = strategy_sol.strategy()
        
        if flag == True:
            _date_sol = False
            try:
                bot.send_message(chat_id_ivan, f"Exited \n bank: {round(strategy_sol.bank, 2)} \n pred_position: {strategy_sol.pred_position}")
            except Exception as e:
                print("Error from telegramm")
                time.sleep(1)
        
        if _date_sol is False:
            try:
                bot.send_message(chat_id_ivan, "Error from bybit")
            except Exception as e:
                print("Error from telegramm")
                time.sleep(1)
            print("Error from bybit")
        else:
            if date != _date_sol:
                date = _date_sol
                try:    
                    bot.send_message(chat_id_ivan, text=json.dumps(report_sol, indent=2, separators=(',', ': ')))
                except Exception as e:
                    print("Error from telegramm")
                    time.sleep(1)
                
                bot.send_message(chat_id_ivan, text=f"start_bank: {100} \n now_bank: {int(report_sol['bank'])} \n profit: {(int(report_sol['bank']) - 100) / 100 * 100}")
                print(datetime.now())
                
        time.sleep(10)
    
    
        
@bot.message_handler(commands=['button'])
def button_message(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("exit from position")
    markup.add(item1)
    bot.send_message(chat_id_ivan, text="choise action:", reply_markup=markup)
 

@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text=="exit from position":
        
        global strategy_sol
        try:
            strategy_sol.exit_from_position()
        except Exception as e:
            print("Error from bybit")
            time.sleep(1)
        
        try:
            bot.send_message(chat_id_ivan, text=f"Exited \n bank: {round(strategy_sol.bank, 2)} \n pred_position: {strategy_sol.pred_position}")
        except Exception as e:
            print("Error from telegramm")
            time.sleep(1)

 
bot.infinity_polling()
