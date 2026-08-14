import os

from arkruntime import Ark

client = Ark()
MODEL = os.environ.get("ENDPOINT_ID", "doubao-seed-2-1-pro-260628")

print("----- tokenization request -----")
resp = client.tokenization.create(
    model=MODEL,
    text=["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
)
print(resp)
