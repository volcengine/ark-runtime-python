import os

from arkruntime import Ark

# Authentication
# 1.If you authorize your endpoint using an API key, you can set your api key to environment variable "ARK_API_KEY"
client = Ark()
MODEL = os.environ.get("ENDPOINT_ID", "doubao-seed-1-6")

if __name__ == "__main__":
    # Streaming:
    print("----- streaming request -----")
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "How many Rs are there in the word 'strawberry'?"},
        ],
        thinking={"type": "enabled"},
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.reasoning_content:
            print(chunk.choices[0].delta.reasoning_content, end="")
        else:
            print(chunk.choices[0].delta.content, end="")
    print()

    # Non-streaming:
    print("----- standard request -----")
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "How many Rs are there in the word 'strawberry'?"},
        ],
        thinking={"type": "enabled"},
    )
    print(completion.choices[0].message.reasoning_content)
    print(completion.choices[0].message.content)
