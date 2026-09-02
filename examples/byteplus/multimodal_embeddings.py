from arkruntime import Ark

client = Ark.byteplus()

print("----- multimodal embeddings request -----")
resp = client.multimodal_embeddings.create(
    model="skylark-embedding-vision-251215",
    input=[
        {"type": "text", "text": "What is the weather like today?"},
        {"type": "image_url", "image_url": {"url": "https://ark-project.tos-cn-beijing.volces.com/images/view.jpeg"}},
    ],
)
print(resp.data)
