import os

from arkruntime import Ark

# Authentication
# 1.If you authorize your endpoint using an API key, you can set your api key to environment variable "ARK_API_KEY"
# or specify api key by Ark.byteplus(api_key="${YOUR_API_KEY}").
# Note: If you use an API key, this API key will not be refreshed.
# To prevent the API from expiring and failing after some time, choose an API key with no expiration date.

# 2.If you authorize your endpoint with BytePlus Identity and Access Management (IAM),
# set your access key and secret key in "BYTEPLUS_ACCESSKEY" and "BYTEPLUS_SECRETKEY"
# or specify ak&sk by Ark.byteplus(ak="${YOUR_AK}", sk="${YOUR_SK}").
client = Ark.byteplus()
MODEL = os.environ.get("ARK_MODEL", "seed-2-0-lite-260428")


if __name__ == "__main__":
    # Non-streaming:
    print("----- standard request -----")
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
            {"role": "user", "content": "常见的十字花科植物有哪些？"},
        ],
    )
    print(completion.choices[0].message.content)

    # Streaming:
    print("----- streaming request -----")
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
            {"role": "user", "content": "常见的十字花科植物有哪些？"},
        ],
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        print(chunk.choices[0].delta.content, end="")
    print()
