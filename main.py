import telebot
import requests
import time
import os
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask

# === CONFIGURAÇÕES ===
NOTION_TOKEN = os.getenv('NOTION_TOKEN', 'ntn_b70490395432oqvvJldbsMBs0H3dbBK0g0GAeEf9VCigUG')
PAGE_ID = os.getenv('PAGE_ID', '2ad1a427ceb7815598cdffb8271f5d43')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8218809414:AAFyiyjZyfBYgWDIiw3vdGC5miW9HreyTlw')
CHAT_ID = int(os.getenv('CHAT_ID', '-1003267500349'))
MENSAGEM = os.getenv('MENSAGEM', "Uma nova resposta foi enviada em 7th Court Roleplay.")
COOLDOWN = timedelta(minutes=3)
HORAS_24 = 24 * 60 * 60

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

last_edited_time = None
last_send_time = datetime.min

# === HEALTH CHECK ===
@app.route('/health')
def health():
    return '7th Court vivo! ❤️', 200

@app.route('/')
def home():
    return '7th Court Monitor - Online', 200

# === APAGA MENSAGEM APÓS 24H ===
def apagar_depois(chat_id, message_id):
    time.sleep(HORAS_24)
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

# === COMANDO /re (100% FUNCIONANDO COM APAGAR + ENVIAR) ===
@bot.message_handler(commands=['re'])
def comando_re(message):
    if message.chat.id != CHAT_ID:
        return
    
    global last_send_time
    agora = datetime.now()
    if agora - last_send_time < COOLDOWN:
        return
    
    # 1. Primeiro envia a mensagem (usando reply_to enquanto o original ainda existe)
    enviado = bot.reply_to(message, MENSAGEM)
    last_send_time = agora
    
    # 2. Agora apaga o /re original
    try:
        bot.delete_message(CHAT_ID, message.message_id)
    except:
        pass
    
    # 3. Agenda apagar a notificação depois de 24h
    Thread(target=apagar_depois, args=(CHAT_ID, enviado.message_id), daemon=True).start()

# === MONITOR NOTION (SÓ ENVIA QUANDO HOUVER EDIÇÃO REAL) ===
def monitor_notion():
    global last_edited_time, last_send_time
    url = f"https://api.notion.com/v1/pages/{PAGE_ID}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }

    # Inicialização
    print("Inicializando monitor do Notion...")
    while True:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                last_edited_time = r.json()["last_edited_time"]
                print(f"Notion inicializado → última edição: {last_edited_time[-12:-4]}")
                break
        except:
            time.sleep(10)

    print("Monitor ativo — só envia com edição real")

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                current = r.json()["last_edited_time"]
                if current != last_edited_time:
                    print(f"EDIÇÃO DETECTADA → {current[-12:-4]}")
                    last_edited_time = current
                    agora = datetime.now()
                    if agora - last_send_time >= COOLDOWN:
                        print("ENVIANDO notificação real")
                        enviado = bot.send_message(CHAT_ID, MENSAGEM)
                        last_send_time = agora
                        Thread(target=apagar_depois, args=(CHAT_ID, enviado.message_id), daemon=True).start()
            time.sleep(5)
        except Exception as e:
            print(f"Erro no monitor Notion: {e}")
            time.sleep(10)

# === INICIALIZAÇÃO FINAL ===
print("7th Court Roleplay BOT + MONITOR — ONLINE 24/7")

# 1. Monitor do Notion em background
Thread(target=monitor_notion, daemon=True).start()

# 2. Flask em background (só pro health check)
def run_flask():
    print("Flask ativo na porta 5000 → health check OK")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

Thread(target=run_flask, daemon=True).start()

# 3. Bot Telegram como processo principal (nunca mais perde /re)
print("Bot Telegram iniciando como principal...")
try:
    bot.infinity_polling(none_stop=True, interval=0, timeout=20)
except Exception as e:
    print(f"Polling caiu → reiniciando em 5s... {e}")
    time.sleep(5)
    bot.infinity_polling(none_stop=True, interval=0, timeout=20)
