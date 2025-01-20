import requests
import json
import get_token


def advice():

    giga_token = get_token.token()
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [
            {"role": "user",
            "content": "Привет, подскажи мне, как человеку, интересующемуся экологией, один совет в отношении утилизации мусора. максимум 2 коротеньких предложения."}
        ],
        "temperature": 0.5,
        "top_p": 1, #Контроль разнообразия ответов
        "n": 1, #Кол-во возвращаемых ответов
        "stream": False, #Потоковая передача ответа
        "max_tokens": 512, #Максимальное количество токенов в ответе
        "repetition_penalty": 1, #Штраф за повторения
        "update_interval": 0 #Интервал обновления (для потоковой передачи)
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {giga_token}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)

    return str(response.json()['choices'][0]['message']['content'])

