"""Image generation examples for the new arkruntime SDK.

Mirrors the legacy `volcenginesdkarkruntime/image_generations.py` walkthrough
(Seedream / Seededit text-to-image and edit-from-image), wired against the
generated `/images/generations` surface. Streaming is omitted — see
`sequential_image_generation` for multi-image generation in one round-trip.
"""

import os

from arkruntime import Ark
from arkruntime.types.images.sequential_image_generation_options_param import (
    SequentialImageGenerationOptionsParam,
)

client = Ark(api_key=os.environ["ARK_API_KEY"])
# Seedream model — used for the text-to-image and sequential examples.
# Override via env vars to point at your own endpoint IDs.
SEEDREAM_MODEL = os.environ.get("SEEDREAM_ENDPOINT_ID", "doubao-seedream-4-0-250828")
# Seededit model — used for the image-edit example. Only Seededit supports
# `size="adaptive"` and the `image=[...]` reference-image input.
SEEDEDIT_MODEL = os.environ.get("SEEDEDIT_ENDPOINT_ID", "doubao-seededit-3-0-i2i-250628")
SEEDEDIT_INPUT_IMAGE_URL = os.environ.get(
    "SEEDEDIT_INPUT_IMAGE_URL",
    "https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream_i2i.jpeg",
)


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

    print("----- [Seededit] generate images (with input image) -----")
    result = client.images.generate(
        model=SEEDEDIT_MODEL,
        prompt="把背景换成黄昏的沙漠",
        image=[SEEDEDIT_INPUT_IMAGE_URL],
        seed=1234567890,
        watermark=True,
        size="adaptive",  # only valid for Seededit i2i
    )
    print(result)

    print("----- [Seedream] sequential image generation -----")
    result = client.images.generate(
        model=SEEDREAM_MODEL,
        prompt="星球大战, 需要三幅图片描绘不同的战斗场景",
        response_format="url",
        seed=1234567890,
        watermark=True,
        size="1024x1024",
        sequential_image_generation="auto",
        sequential_image_generation_options=SequentialImageGenerationOptionsParam(max_images=3),
    )
    for i, item in enumerate(result.data or []):
        print(f"[{i}] size={item.size} url={item.url}")
    if result.usage is not None:
        print("usage:", result.usage)
