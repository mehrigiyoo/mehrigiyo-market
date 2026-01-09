import datetime
import requests

from paymeuz.keywords import TELEGRAM_CONSULTATION_GROUP_ID, TG_SEND_MESSAGE
from specialist.models import AdviceTime


def notify_doctors(advice_id: int, start_time: str, end_time: str) -> dict:
    advice = AdviceTime.objects.get(id=advice_id)

    doctor_slug = advice.doctor.full_name.lower().replace(' ', '_')

    message = f"#konsultatsiya #{doctor_slug}\n\n"

    message += f"<b>Doktor</b>: {advice.doctor.full_name}\n"
    message += f"<b>Patsient</b>: {advice.client.get_full_name()}\n"
    message += f"<b>Telefon raqam</b>: {advice.client.username}\n"

    message += f"<b>Uchrashuv vaqti</b>: {start_time} - {end_time}"

    response = requests.post(TG_SEND_MESSAGE, dict({
        "chat_id": TELEGRAM_CONSULTATION_GROUP_ID,
        "parse_mode": "HTML",
        "text": message
    }))
    result = response.json()

    return result
