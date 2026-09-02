import os

from arkruntime import Ark

client = Ark.byteplus()
MODEL = os.environ.get("ENDPOINT_ID", "seed-2-0-lite-260428")

print("----- tokenization request -----")
resp = client.tokenization.create(
    model=MODEL,
    text=["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
)
print(resp)
