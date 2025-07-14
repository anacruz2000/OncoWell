import requests

API_KEY = "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"  # Replace with your OpenRouter API key
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def chatbot_response(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    # System prompt com contexto de profissional de saúde especializado em oncologia
    system_prompt = (
        "És um profissional de saúde especializado em oncologia com vasta experiência no acompanhamento de doentes oncológicos. "
        "A tua função é avaliar as respostas dos pacientes de forma empática e profissional, considerando:\n\n"
        "1. **Estado emocional**: Avalia sinais de ansiedade, depressão, esperança, resiliência\n"
        "2. **Compreensão da doença**: Verifica se o paciente compreende o seu diagnóstico e tratamento\n"
        "3. **Coping mechanisms**: Identifica estratégias de adaptação positivas ou negativas\n"
        "4. **Rede de apoio**: Avalia a presença e qualidade do apoio familiar/social\n"
        "5. **Adesão ao tratamento**: Identifica sinais de compliance ou dificuldades\n"
        "6. **Qualidade de vida**: Avalia impacto da doença na vida quotidiana\n\n"
        "Classifica a resposta num tópico (ex: Tratamentos, Sintomas, Apoio emocional, Qualidade de vida, etc) "
        "e fornece uma avaliação clínica breve."
        "Seja sempre empático e profissional na avaliação."
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

def avaliar_resposta_journaling(resposta_texto, pergunta_texto=None):
    """
    Avalia uma resposta de journaling com contexto oncológico
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Contexto específico para avaliação de journaling oncológico
    system_prompt = (
        "És um oncologista experiente especializado em cuidados paliativos e apoio psicológico a doentes oncológicos. "
        "A tua missão é avaliar as respostas de journaling dos pacientes considerando:\n\n"
        "**Avaliação Clínica:**\n"
        "- Estado emocional (ansiedade, depressão, esperança, aceitação)\n"
        "- Compreensão da doença e tratamento\n"
        "- Estratégias de coping (positivas/negativas)\n"
        "- Qualidade da rede de apoio\n"
        "- Adesão ao tratamento\n"
        "- Impacto na qualidade de vida\n\n"
        "**Classificação de Risco:**\n"
        "- Estável: Paciente estável, bem adaptado, rede de apoio forte\n"
        "- Moderado: Algumas preocupações, mas coping adequado\n"
        "- Crítico: Sinais de sofrimento significativo, isolamento, desesperança\n\n"
        "**Recomendações:**\n"
        "- Sugestões específicas para melhorar o bem-estar\n"
        "- Recursos ou intervenções recomendadas\n\n"
    )
    
    # Construir o prompt com contexto
    if pergunta_texto:
        user_prompt = f"Pergunta: {pergunta_texto}\nResposta do paciente: {resposta_texto}"
    else:
        user_prompt = f"Reflexão livre do paciente: {resposta_texto}"
    
    payload = {
        "model": "deepseek/deepseek-chat:free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
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