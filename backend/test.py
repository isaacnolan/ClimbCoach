import openai

openai.api_key = "sk-proj-1234567890"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello, how are you?"}])

print(response)