import os
from groq import Groq

def main():
    client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    models = client.models.list()
    print("Active Models on Groq:")
    for model in models.data:
        print(f"- ID: {model.id} (Created by: {model.owned_by})")

if __name__ == "__main__":
    main()
