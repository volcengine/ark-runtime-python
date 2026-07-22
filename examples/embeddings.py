import os

from arkruntime import Ark

client = Ark()
MODEL = os.environ.get("ENDPOINT_ID", "doubao-embedding-text-240715")

print("----- embeddings request -----")
resp = client.embeddings.create(
    model=MODEL,
    input=["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
)
print(resp)
