# utils/telegram.py yarating
def send_to_bot(message):
    import requests

    BOT_TOKEN = "8548867982:AAFGIC_qA4CK0iQSiJdt1IeCjjm5pLS0TaU"
    OPERATOR_CHAT_ID = "7664935217"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, json={
        "chat_id": OPERATOR_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    })