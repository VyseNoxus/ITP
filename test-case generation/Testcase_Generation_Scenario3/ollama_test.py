import requests

# API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"

def ask_ollama(model, prompt):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # Set to True if you want live output
    }

    try:
        response = requests.post(OLLAMA_API, json=payload)
        response.raise_for_status()  # Raise error on bad HTTP status
        return response.json()['response']
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Ollama: {e}")
        return None

if __name__ == "__main__":
    model_name = "mistral"
    user_prompt = "Hi ollama!"

    print("Asking Ollama...")
    answer = ask_ollama(model_name, user_prompt)

    if answer:
        print("\n=== Response ===\n")
        print(answer)

        # Save to file
        with open("ollama_response.txt", "w", encoding="utf-8") as f:
            f.write("Prompt:\n")
            f.write(user_prompt)
            f.write("\n\nResponse:\n")
            f.write(answer)

        print("\n✅ Response saved to 'ollama_response.txt'")
    else:
        print("No response received.")