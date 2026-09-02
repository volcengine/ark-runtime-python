import os

from arkruntime import Ark

client = Ark.byteplus()

response = client.responses.create(
    model=os.environ.get("ARK_MODEL", "seed-2-0-lite-260428"),
    input="Explain large language models in one sentence.",
)
for item in response.output or []:
    if item.type == "message":
        for content in item.content:
            if content.type == "output_text":
                print(content.text)
