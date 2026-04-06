from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

QUESTIONS = {
    1: {
        "text": "Hola ¿Cómo estás? 👋\n¿Qué tipo de compra estás interesado en hacer en Winie Deco & Hogar?\n\n"
                "a) Para comercio / Revender / Un emprendimiento.\n"
                "b) Para uso personal.\n"
                "c) Soy cliente.",
        "options": ["a", "b", "c"]
    },
    2: {
        "text": "¿Qué tipo de información estás buscando?\n\n"
                "a) Información sobre nuestra página web.\n"
                "b) Información sobre cómo comprar en nuestros locales.\n"
                "c) Información sobre los rubros que trabajamos en Winie.\n"
                "d) Tengo otra consulta.",
        "options": ["a", "b", "c", "d"]
    }
}

RESPONSES = {
    "b_cliente": "Disculpa, no trabajamos con este tipo de clientes. ¡Gracias por tu interés!",
    "c_cliente": "Espera unos minutos, ya te atiende uno de los chicos.",
    "web": "Podés visitar nuestra página web en: https://www.winiedeco.com",
    "locales": "Podés comprar en nuestros locales de Córdoba. Te esperamos con atención personalizada y stock disponible.",
    "rubros": "En Winie Deco & Hogar trabajamos con distintos rubros:\n"
              "- 🌿 Plantas Artificiales\n"
              "- ✨ Línea Holística (velas, sahumerios, aromas)\n"
              "- 🏠 Deco & Hogar (cuadros, adornos, objetos)\n"
              "- 🍳 Cocina (utensilios y accesorios)\n"
              "- 📦 Organización (cestos, organizadores)\n\n"
              "Un representante te seguirá atendiendo en breve.",
    "otra": "Espera unos minutos, ya te atiende uno de los chicos."
}

# --- Funciones auxiliares ---
def get_user_state(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT question_id FROM states WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_user_state(user_id, question_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    if question_id is None:
        c.execute("DELETE FROM states WHERE user_id=?", (user_id,))
    else:
        c.execute("INSERT OR REPLACE INTO states (user_id, question_id) VALUES (?, ?)", (user_id, question_id))
    conn.commit()
    conn.close()

def save_answer(user_id, question_id, answer):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("INSERT INTO answers (user_id, question_id, answer) VALUES (?, ?, ?)", (user_id, question_id, answer))
    conn.commit()
    conn.close()

def get_client_type(user_id):
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("SELECT answer FROM answers WHERE user_id=? AND question_id=1", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# --- Webhook ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    user_id = data["from"]
    message = data["text"]["body"].strip().lower()

    client_type = get_client_type(user_id)
    current_q = get_user_state(user_id)

    # Si ya sabemos que es comerciante o cliente, no lo filtramos más
    if client_type in ["a", "c"]:
        if current_q is None:
            set_user_state(user_id, 2)
            send_whatsapp_message(user_id, QUESTIONS[2]["text"])
            return "ok", 200

    # Flujo normal
    if current_q is None:
        set_user_state(user_id, 1)
        send_whatsapp_message(user_id, QUESTIONS[1]["text"])
        return "ok", 200

    elif current_q == 1:
        if message == "a":
            save_answer(user_id, 1, "a")
            set_user_state(user_id, 2)
            send_whatsapp_message(user_id, QUESTIONS[2]["text"])
            return "ok", 200
        elif message == "b":
            send_whatsapp_message(user_id, RESPONSES["b_cliente"])
            return "ok", 200
        elif message == "c":
            save_answer(user_id, 1, "c")
            send_whatsapp_message(user_id, RESPONSES["c_cliente"])
            return "ok", 200

    elif current_q == 2:
        if message == "a":
            save_answer(user_id, 2, "web")
            set_user_state(user_id, None)
            send_whatsapp_message(user_id, RESPONSES["web"])
            return "ok", 200
        elif message == "b":
            save_answer(user_id, 2, "locales")
            set_user_state(user_id, None)
            send_whatsapp_message(user_id, RESPONSES["locales"])
            return "ok", 200
        elif message == "c":
            save_answer(user_id, 2, "rubros")
            set_user_state(user_id, None)
            send_whatsapp_message(user_id, RESPONSES["rubros"])
            return "ok", 200
        elif message == "d":
            save_answer(user_id, 2, "otra consulta")
            set_user_state(user_id, None)
            send_whatsapp_message(user_id, RESPONSES["otra"])
            return "ok", 200

# --- Inicialización BD ---
def init_db():
    conn = sqlite3.connect("bot.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS states (user_id TEXT PRIMARY KEY, question_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS answers (user_id TEXT, question_id INTEGER, answer TEXT)")
    conn.commit()
    conn.close()



import requests
import os

ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")  # lo guardás como variable de entorno
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


if __name__ == "__main__":
    init_db()
    app.run(port=5000, debug=True)



