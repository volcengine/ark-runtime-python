import os

from arkruntime import Ark

# Authentication
# 1.If you authorize your endpoint using an API key, you can set your api key to environment variable "ARK_API_KEY"
# or specify api key by Ark(api_key="${YOUR_API_KEY}").
client = Ark()
MODEL = os.environ.get("ENDPOINT_ID", "doubao-seed-1-6")

# Image input:
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "这是哪里？"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://ark-project.tos-cn-beijing.volces.com/images/view.jpeg"},
                },
            ],
        }
    ],
)

print(response.choices[0])
