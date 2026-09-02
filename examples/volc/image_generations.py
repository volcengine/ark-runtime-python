"""Seedream image generation examples for the new arkruntime SDK."""

import os

from arkruntime import Ark

client = Ark.volc(api_key=os.environ["ARK_API_KEY"])
# Seedream model — used for the text-to-image example.
# Override via env vars to point at your own endpoint IDs.
SEEDREAM_MODEL = os.environ.get("SEEDREAM_ENDPOINT_ID", "doubao-seedream-5-0-pro-260628")


if __name__ == "__main__":
    print("----- [Seedream] generate images -----")
    result = client.images.generate(
        model=SEEDREAM_MODEL,
        prompt="龙与地下城女骑士背景是起伏的平原，目光从镜头转向平原",
        seed=1234567890,
        watermark=True,
        size="1024x1024",
    )
    print(result)
