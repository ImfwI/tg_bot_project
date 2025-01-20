#Получение токена
import requests
import uuid
import urllib3


def token():
    urllib3.disable_warnings()

    GigaChatKey = 'KEY'

    rq_uid = str(uuid.uuid4())
    #URL API, к которому мы обращаемся
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    #Данные для запроса
    payload={
        'scope': 'GIGACHAT_API_PERS'
    }
    #Заголовки запроса
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': rq_uid,
        'Authorization': f'Basic {GigaChatKey}'
    }


    response = requests.request("POST", url, headers=headers, data=payload, verify=False)

    giga_token = str(response.text[response.text.find(':"') + 2 : response.text.find('",')])

    return giga_token
