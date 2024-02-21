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


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Start bot')
    
    
    
    
        
@bot.message_handler(commands=['button'])
def button_message(message):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("exit from position")
    markup.add(item1)
    bot.send_message(chat_id_ivan, text="choise action:",reply_markup=markup)
 
 
 
 
 

@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text=="exit from position":
        bot.send_message(chat_id_ivan, text="Hello")

 
bot.infinity_polling()
