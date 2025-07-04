import requests

API_KEY = "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"  # Replace with your OpenRouter API key
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def chatbot_response(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    # Novo prompt para pedir topico e resposta em JSON
    system_prompt = (
        "Classifica a seguinte pergunta num tópico (ex: Tratamentos, Sintomas, Apoio emocional, etc) "
        "e responde à pergunta. Devolve o resultado no formato JSON: {\"topico\": ..., \"resposta\": ...}. "
        "Se não souber o tópico, tenta adivinhar o mais aproximado."
    )
    payload = {
        "model": "deepseek/deepseek-chat:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.RequestException as req_err:
        return f"Request error occurred: {req_err}"
    except KeyError:
        return "Error: Unexpected response format from the API."

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "stop"]:
            break
        response = chatbot_response(user_input)
        print("Chatbot:", response)