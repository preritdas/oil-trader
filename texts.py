# Non-local imports
import nexmo

# Local imports
import _keys

# Instantiate Nexmo client
nexmo_client = nexmo.Client(
    key = _keys.nexmo_api_key,
    secret = _keys.nexmo_api_secret 
)

# Instantiate sms object
sms = nexmo.Sms(client = nexmo_client)

# For alert_once. Already texted strings
already_texted = []

def text_me(message: str, alert_once: bool = False, alert_once_override: bool = False):
    global already_texted

    if message not in already_texted and alert_once_override == False:
        response = sms.send_message(
            {
                "from": _keys.nexmo_sender,
                "to": _keys.nexmo_my_number,
                "text": message
            }
        )

    # Alert_once logic
    if alert_once:
        already_texted.append(message)

    return True if response["messages"][0]["status"] == '0' else False