import requests
import config


def gpt(text):
    prompt = {
        "modelUri": f"gpt://{config.id_ya}/yandexgpt",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                'role': 'system',
                'text': '''
Ты ИИ-помощник, который анализирует текст пользователя. Твоя задача:
1. Определить основную тему текста.
2. Сделать краткое содержание (1–3 предложения).
3. Определить настроение текста (позитивное, негативное, нейтральное).
4. Определить тип текста (например: новость, отзыв, рассказ, инструкция и т.д.).

Отвечай строго по шаблону:

📌 Тема: ...
🧠 Суть: ...
😊 Настроение: ...
🔎 Тип текста: ...
'''
            },
            {
                "role": "user",
                "text": text
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {config.key_ya}"
    }

    response = requests.post(url, headers=headers, json=prompt)
    result = response.json().get('result')
    return result['alternatives'][0]['message']['text']
