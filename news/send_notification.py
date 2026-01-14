import os
import firebase_admin
from firebase_admin import credentials, messaging


def get_firebase_app():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred_path = os.getenv("FIREBASE_CRED_PATH")

    if not cred_path:
        raise RuntimeError("FIREBASE_CRED_PATH is not set")

    if not os.path.isfile(cred_path):
        raise RuntimeError(f"Firebase credential file not found: {cred_path}")

    cred = credentials.Certificate(cred_path)
    return firebase_admin.initialize_app(cred)


def sendPush(title, description, registration_tokens, image=None, dataObject=None):
    if not registration_tokens:
        return None

    get_firebase_app()

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=description,
            image=image,
        ),
        data=dataObject or {},
        tokens=registration_tokens,
    )

    return messaging.send_multicast(message)





# import firebase_admin
# from firebase_admin import credentials, messaging
#
# cred = credentials.Certificate("config/doctor-ali-firebase-adminsdk-hujjz-7b33529111.json")
# firebase_admin.initialize_app(cred)
#
#
# def sendPush(title, description, registration_tokens, image=None, notification_name=None, dataObject=None):
#     # See documentation on defining a message payload.
#     message = messaging.MulticastMessage(
#         notification=messaging.Notification(
#             title=title,
#             body=description,
#             image=image,
#         ),
#         data=dataObject,
#         tokens=registration_tokens,
#     )
#
#     # Send a message to the device corresponding to the provided
#     # registration token.
#     response = messaging.send_multicast(message)
#     # Response is a message ID string.
#     return response