import os

from arkruntime import Ark

client = Ark.volc()

response = client.responses.create(
    model=os.environ.get("ARK_MODEL", "doubao-seed-2-1-pro-260628"),
    input="Explain large language models in one sentence.",
)
for item in response.output or []:
    if item.type == "message":
        for content in item.content:
            if content.type == "output_text":
                print(content.text)
