# main.py — 7th Court Roleplay (FINAL – só subir e esquecer)
import telebot
import requests
import time
from datetime import datetime, timedelta
from threading import Thread, Timer

# === CONFIGURAÇÕES FINAIS (tudo preenchido) ===
NOTION_TOKEN   = 'ntn_b70490395432oqvvJldbsMBs0H3dbBK0g0GAeEf9VCigUG'
PAGE_ID        = '2ad1a427ceb7815598cdffb8271f5d43'
TELEGRAM_TOKEN = '8218809414:AAFyiyjZyfBYgWDIiw3vdGC5miW9HreyTlw'
CHAT_ID        = -1003267500349                     # ← seu grupo real

MENSAGEM = "Uma nova resposta foi enviada em 7th Court Roleplay."
COOLDOWN = timedelta(minutes=3)
HORAS_24 = 24 * 60 * 60  # 86400 segundos

bot = telebot.TeleBot(TELEGRAM_TOKEN)
last_edited_time = None
last_send_time = datetime.min

# === APAGA MENSAGEM DEPOIS DE 24 HORAS ===
def apagar_depois(chat_id, message_id):
    Timer(HORAS_24, lambda: bot.delete_message(chat_id, message_id)).start()

# === COMANDO /re (manual) ===
@bot.message_handler(commands=['re'])
def comando_re(message):
    if message.chat.id != CHAT_ID:
        return
    agora = datetime.now()
    if agora - last_send_time < COOLDOWN:
        return
    enviado = bot.reply_to(message, MENSAGEM)
    global last_send_time
    last_send_time = agora

    # Apaga o /re imediatamente
    try:
        bot.delete_message(CHAT_ID, message.message_id)
    except:
        pass

    # Programa a notificação pra sumir em 24h
    apagar_depois(CHAT_ID, enviado.message_id)

# === MONITOR NOTION (automático) ===
def monitor_notion():
    global last_edited_time, last_send_time
    url = f"https://api.notion.com/v1/pages/{PAGE_ID}"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}
    while True:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                current = r.json()["last_edited_time"]
                if current != last_edited_time:
                    agora = datetime.now()
                    if agora - last_send_time >= COOLDOWN:
                        enviado = bot.send_message(CHAT_ID, MENSAGEM)
                        print(f"[{agora.strftime('%H:%M:%S')}] Notificação automática enviada")
                        last_send_time = agora
                        apagar_depois(CHAT_ID, enviado.message_id)
                    last_edited_time = current
        except Exception as e:
            print(f"Erro monitor: {e}")
        time.sleep(30)

print("7th Court Roleplay BOT + MONITOR — ONLINE 24/7")
Thread(target=monitor_notion, daemon=True).start()
bot.infinity_polling()
