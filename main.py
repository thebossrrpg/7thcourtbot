import telebot
import requests
import time
from datetime import datetime, timedelta
from threading import Thread, Timer
from flask import Flask

# === CONFIGURAÇÕES ===
NOTION_TOKEN   = 'ntn_b70490395432oqvvJldbsMBs0H3dbBK0g0GAeEf9VCigUG'
PAGE_ID        = '2ad1a427ceb7815598cdffb8271f5d43'
TELEGRAM_TOKEN = '8218809414:AAFyiyjZyfBYgWDIiw3vdGC5miW9HreyTlw'
CHAT_ID        = -1003267500349

MENSAGEM = "Uma nova resposta foi enviada em 7th Court Roleplay."
COOLDOWN = timedelta(minutes=3)
HORAS_24 = 24 * 60 * 60

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

last_edited_time = None
last_send_time = datetime.min

# === FLASK HEALTH CHECK ===
@app.route('/health')
def health():
    return '7th Court vivo! ❤️', 200

@app.route('/')
def home():
    return '7th Court Monitor - Online', 200

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

# === MONITOR NOTION COM DEBOUNCE 30s + COOLDOWN 3min + GRACE 30s ===
def monitor_notion():
    global last_edited_time, last_send_time
    url = f"https://api.notion.com/v1/pages/{PAGE_ID}"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}
    
    pending_debounce = None
    
    def tentar_enviar():
        nonlocal pending_debounce
        global last_send_time
        agora = datetime.now()
        if agora - last_send_time >= COOLDOWN:
            print(f"[{agora.strftime('%H:%M:%S')}] Verificando cooldown: OK")
            # VERIFICAÇÃO EXTRA: confirma se ainda não houve edição recente
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200 and r.json()["last_edited_time"] == last_edited_time:
                enviado = bot.send_message(CHAT_ID, MENSAGEM)
                print(f"[{agora.strftime('%H:%M:%S')}] Notificação ENVIADA!")
                last_send_time = agora
                apagar_depois(CHAT_ID, enviado.message_id)
            else:
                print("Edição aconteceu DENTRO dos 30s, cancelando envio")
        pending_debounce = None

    while True:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                current = r.json()["last_edited_time"]
                if current != last_edited_time:
                    print(f"Edição detectada → {current[-12:-4]}")
                    
                    # VERIFICA COOLDOWN ANTES de agendar
                    agora = datetime.now()
                    if agora - last_send_time < COOLDOWN:
                        print(f"Cooldown ativo: {(COOLDOWN-(agora-last_send_time)).seconds}s restantes")
                        last_edited_time = current  # Atualiza mas NÃO agenda
                        continue
                    
                    last_edited_time = current
                    if pending_debounce:
                        pending_debounce.cancel()
                    pending_debounce = Timer(30, tentar_enviar)
                    pending_debounce.start()
                    print("⏳ Timer 30s iniciado - aguardando confirmação final...")
        except Exception as e:
            print(f"Erro monitor: {e}")
        time.sleep(10)  # Mais responsivo

# === FUNÇÃO PARA RODAR O BOT ===
def run_bot():
    time.sleep(3)  # Aguarda 3s antes de iniciar
    print("Iniciando bot Telegram...")
    try:
        bot.infinity_polling(none_stop=True, interval=0, timeout=20)
    except Exception as e:
        print(f"Erro fatal no polling: {e}")

# === INICIALIZAÇÃO ===
print("7th Court Roleplay BOT + MONITOR — ONLINE 24/7")

# Inicia o monitor do Notion
Thread(target=monitor_notion, daemon=True).start()

# Inicia o bot do Telegram em thread separada
Thread(target=run_bot, daemon=True).start()

# Inicia o Flask (PRINCIPAL - mantém o processo vivo)
if __name__ == '__main__':
    print("Iniciando servidor Flask na porta 8000...")
    app.run(host='0.0.0.0', port=8000, debug=False)
