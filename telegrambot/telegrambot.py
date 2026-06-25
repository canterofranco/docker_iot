from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

import paho.mqtt.client as mqtt
import logging
import json
import ssl
import os

# --------------------------------------------------
# CONFIGURACION
# --------------------------------------------------

TOKEN = os.environ["TB_TOKEN"]
ID_DISPOSITIVO = os.environ["ID_DISPOSITIVO"]

estado_actual = {}

logging.basicConfig(
    format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --------------------------------------------------
# MQTT
# --------------------------------------------------

def on_connect(client, userdata, flags, rc, properties=None):
    logging.info("Conectado al broker MQTT")

    client.subscribe(ID_DISPOSITIVO)

def on_message(client, userdata, msg):
    global estado_actual

    try:
        payload = msg.payload.decode()

        logging.info(
            f"MQTT RX -> {msg.topic}: {payload}"
        )

        estado_actual = json.loads(payload)

    except Exception as e:
        logging.error(f"Error MQTT RX: {e}")

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

mqtt_client.username_pw_set(
    os.environ["MQTT_USR"],
    os.environ["MQTT_PASS"]
)

mqtt_client.tls_set(
    cert_reqs=ssl.CERT_REQUIRED
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# --------------------------------------------------
# FUNCION PUBLICAR
# --------------------------------------------------

def publicar(topico, mensaje):

    mqtt_client.publish(
        topico,
        str(mensaje)
    )

    logging.info(
        f"MQTT TX -> {topico}: {mensaje}"
    )

# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    kb = [
        ["/estado"],
        ["/modo automatico"],
        ["/modo manual"],
        ["/rele 1", "/rele 0"],
        ["/destello"]
    ]

    await update.message.reply_text(
        "Bot de control del termostato IoT",
        reply_markup=ReplyKeyboardMarkup(
            kb,
            resize_keyboard=True
        )
    )

async def acercade(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Bot para control de termostato mediante MQTTs."
    )

# --------------------------------------------------
# ESTADO
# --------------------------------------------------

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not estado_actual:

        await update.message.reply_text(
            "Aún no se recibieron datos del termostato."
        )

        return

    texto = (
        f"Temperatura: {estado_actual.get('temperatura', '-') } °C\n"
        f"Humedad: {estado_actual.get('humedad', '-') } %\n"
        f"Setpoint: {estado_actual.get('setpoint', '-') }\n"
        f"Periodo: {estado_actual.get('periodo', '-') } s\n"
        f"Modo: {estado_actual.get('modo', '-') }"
    )

    await update.message.reply_text(texto)

# --------------------------------------------------
# SETPOINT
# --------------------------------------------------

async def setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Uso: /setpoint <valor>"
        )

        return

    try:

        valor = float(context.args[0])

        publicar(
            f"{ID_DISPOSITIVO}/setpoint",
            valor
        )

        await update.message.reply_text(
            f"Setpoint actualizado a {valor}"
        )

    except ValueError:

        await update.message.reply_text(
            "Valor inválido."
        )

# --------------------------------------------------
# PERIODO
# --------------------------------------------------

async def periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Uso: /periodo <segundos>"
        )

        return

    try:

        valor = int(context.args[0])

        publicar(
            f"{ID_DISPOSITIVO}/periodo",
            valor
        )

        await update.message.reply_text(
            f"Periodo actualizado a {valor} s"
        )

    except ValueError:

        await update.message.reply_text(
            "Valor inválido."
        )

# --------------------------------------------------
# MODO
# --------------------------------------------------

async def modo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Uso: /modo manual | automatico"
        )

        return

    valor = context.args[0].lower()

    if valor not in ["manual", "automatico"]:

        await update.message.reply_text(
            "Modo inválido."
        )

        return

    publicar(
        f"{ID_DISPOSITIVO}/modo",
        valor
    )

    await update.message.reply_text(
        f"Modo actualizado a {valor}"
    )

# --------------------------------------------------
# RELE
# --------------------------------------------------

async def rele(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:

        await update.message.reply_text(
            "Uso: /rele 0 | 1"
        )

        return

    valor = context.args[0]

    if valor not in ["0", "1"]:

        await update.message.reply_text(
            "Valor inválido."
        )

        return

    publicar(
        f"{ID_DISPOSITIVO}/rele",
        valor
    )

    await update.message.reply_text(
        f"Relé = {valor}"
    )

# --------------------------------------------------
# DESTELLO
# --------------------------------------------------

async def destello(update: Update, context: ContextTypes.DEFAULT_TYPE):

    publicar(
        f"{ID_DISPOSITIVO}/destello",
        "1"
    )

    await update.message.reply_text(
        "Destello activado."
    )

# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    mqtt_client.connect(
        os.environ["SERVIDOR"],
        int(os.environ["PUERTO_MQTTS"]),
        60
    )

    mqtt_client.loop_start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("acercade", acercade))
    application.add_handler(CommandHandler("estado", estado))
    application.add_handler(CommandHandler("setpoint", setpoint))
    application.add_handler(CommandHandler("periodo", periodo))
    application.add_handler(CommandHandler("modo", modo))
    application.add_handler(CommandHandler("rele", rele))
    application.add_handler(CommandHandler("destello", destello))

    application.run_polling()

if __name__ == "__main__":
    main()