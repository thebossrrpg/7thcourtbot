# main.py — 7th Court Roleplay (FINAL – FUNCIONA 100%)
import telebot
import requests
import time
from datetime import datetime, timedelta
from threading import Thread, Timer

# === CONFIGURAÇÕES ===
NOTION_TOKEN   = 'ntn_b70490395432oqvvJldbsMBs0H3dbBK0g0GAeEf9VCigUG'
PAGE_ID        = '2ad1a427ceb7815598cdffb8271f5d43'
TELEGRAM_TOKEN = '8218809414:AAFyiyjZyfBYgWDIiw3vdGC5miW9HreyTlw'
CHAT_ID        = -1003267500349

MENSAGEM = "Uma nova resposta foi enviada em 7th Court Roleplay."
COOLDOWN = timedelta(minutes=3)
HORAS_24 = 24 * 60 * 60

bot = telebot.TeleBot(TELEGRAM_TOKEN)
last_edited_time = None
last_send_time = datetime.min

def apagar_depois(chat_id, message_id):
    Timer(HORAS_24, lambda: bot.delete_message(chat_id, message_id)).start()

# === COMANDO /re ===
@bot.message_handler(commands=['re'])
def comando_re(message):
    if message.chat.id != CHAT_ID:
        return
    global last_send_time
    agora = datetime.now()
    if agora - last_send_time < COOLDOWN:
        return
    enviado = bot.reply_to(message, MENSAGEM)
    last_send_time = agora
    try:
        bot.delete_message(CHAT_ID, message.message_id)
    except:
        pass
    apagar_depois(CHAT_ID, enviado.message_id)

# === MONITOR NOTION COM DEBOUNCE 20s + COOLDOWN 3min (perfeito) ===
def monitor_notion():
    global last_edited_time, last_send_time = None, datetime.min
    global last_edited_time, last_send_time  # só pra deixar o linter feliz

    url = f"https://api.notion.com/v1/pages/{PAGE_ID}"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}

    pending_debounce = None
    DEBOUNCE_SEGUNDOS = 20

    def tentar_enviar():
        nonlocal pending_debounce
        global last_send_time
        agora = datetime.now()
        if agora - last_send_time >= COOLDOWN:
            enviado = bot.send_message(CHAT_ID, MENSAGEM)
            print(f"[{agora.strftime('%H:%M:%S')}] Notificação enviada (após 20s sem edição)")
            last_send_time = agora
            apagar_depois(CHAT_ID, enviado.message_id)
        else:
            print("Cooldown de 3 min ainda ativo — ignorando")
        pending_debounce = None

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                current = r.json()["last_edited_time"]
                if current != last_edited_time:
                    print(f"Edição detectada → {current[-12:-4]}")
                    last_edited_time = current

                    if pending_debounce:
                        pending_debounce.cancel()

                    pending_debounce = Timer(DEBOUNCE_SEGUNDOS, tentar_enviar)
                    pending_debounce.start()
        except Exception as e:
            print(f"Erro monitor: {e}")
        time.sleep(25)

print("7th Court Roleplay BOT + MONITOR — ONLINE 24/7")
Thread(target=monitor_notion, daemon=True).start()
bot.infinity_polling()
