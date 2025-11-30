# main.py — 7th Court Roleplay (corrigido pro Koyeb)
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

# === COMANDO /re (corrigido) ===
@bot.message_handler(commands=['re'])
def comando_re(message):
    if message.chat.id != CHAT_ID:
        return

    global last_send_time                     # ← movido pra cima
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

# === MONITOR NOTION COM DEBOUNCE INTELIGENTE ===
def monitor_notion():
    global last_edited_time, last_send_time

    url = f"https://api.notion.com/v1/pages/{PAGE_ID}"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}

    debounce_timer = None          # timer pra esperar parar de editar
    DEBOUNCE_SEGUNDOS = 20         # ← muda aqui se quiser 15s, 30s, etc.

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                current = r.json()["last_edited_time"]

                if current != last_edited_time:
                    print(f"Edição detectada às {datetime.now().strftime('%H:%M:%S')}")

                    last_edited_time = current

                    # Cancela timer anterior (se ainda estiver rodando)
                    if debounce_timer:
                        debounce_timer.cancel()

                    # Cria novo timer: só vai disparar se parar de editar por 20s
                    debounce_timer = Timer(DEBOUNCE_SEGUNDOS, lambda: tentar_enviar())
                    debounce_timer.start()

        except Exception as e:
            print(f"Erro monitor: {e}")

        time.sleep(25)  # checa a cada ~25s (economiza requests)

# Função separada pra tentar enviar (chamada pelo debounce)
def tentar_enviar():
    global last_send_time
    agora = datetime.now()

    # Só envia se já passaram 3 minutos desde a última notificação
    if agora - last_send_time >= COOLDOWN:
        enviado = bot.send_message(CHAT_ID, MENSAGEM)
        print(f"[{agora.strftime('%H:%M:%S')}] Notificação enviada (após debounce)")
        last_send_time = agora
        apagar_depois(CHAT_ID, enviado.message_id)
    else:
        print("Debounce completou, mas ainda dentro do cooldown de 3 min — ignorando")

print("7th Court Roleplay BOT + MONITOR — ONLINE 24/7")
Thread(target=monitor_notion, daemon=True).start()
bot.infinity_polling()
