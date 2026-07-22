import os

from arkruntime import Ark

# Authentication
# 1. If you authorize your endpoint using an API key, you can set your api key
#    to environment variable "ARK_API_KEY" or pass it via Ark(api_key="...").
#    Note: API keys do not refresh — pick one with no expiration.
client = Ark()

# Override these env vars to point at your own model + reference image.
MODEL = os.environ.get("SEEDANCE_MODEL", "doubao-seedance-2-0-fast-260128")
IMAGE_URL = os.environ.get(
    "SEEDANCE_IMAGE_URL",
    "https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_i2v.png",
)


if __name__ == "__main__":
    print("----- create request (i2v) -----")
    # Note: `service_tier` + `execution_expires_after` are NOT accepted by
    # the default seedance-2-0-fast model (server rejects them as
    # InvalidParameter). If your account has access to a model that supports
    # service tiers (e.g. one of the legacy seedance 1.0 endpoints), set
    # `SEEDANCE_MODEL` and uncomment the corresponding kwargs below.
    create_result = client.content_generation.tasks.create(
        model=MODEL,
        content=[
            {
                "type": "text",
                "text": "龙与地下城女骑士背景是起伏的平原，目光从镜头转向平原",
            },
            {
                "type": "image_url",
                "image_url": {"url": IMAGE_URL},
                # "role": "first_frame",
            },
        ],
        # callback_url="${YOUR_CALLBACK_URL}",
    )
    print(create_result)

    print("----- get request -----")
    get_result = client.content_generation.tasks.get(create_result.id)
    print(get_result)
    print("ServiceTier:", getattr(get_result, "service_tier", None))
    print("ExecutionExpiresAfter:", getattr(get_result, "execution_expires_after", None))

    print("----- list request -----")
    list_result = client.content_generation.tasks.list(
        page_num=1,
        page_size=10,
        status="queued",  # one of: queued, running, succeeded, failed, cancelled
        # model=MODEL,
        # task_ids=["test-id-1", "test-id-2"],
    )
    print(list_result)
    if list_result.items:
        print("List Item ServiceTier:", getattr(list_result.items[0], "service_tier", None))
        print("List Item ExecutionExpiresAfter:", getattr(list_result.items[0], "execution_expires_after", None))

    print("----- delete request -----")
    try:
        client.content_generation.tasks.delete(create_result.id)
        print(create_result.id)
    except Exception as e:
        print(f"failed to delete task: {e}")

    # ---- text-only (t2v) flow: create + GET + LIST + DELETE ----
    # `service_tier` + `execution_expires_after` are only valid on models
    # that expose service-tier billing; the default fast model rejects
    # them. Uncomment if you've switched `SEEDANCE_MODEL` to one that does.
    print("----- create request (t2v) -----")
    create_result_flex = client.content_generation.tasks.create(
        model=MODEL,
        content=[
            {
                "type": "text",
                "text": "纯文本生成视频测试",
            }
        ],
        # service_tier="flex",
        # execution_expires_after=3600,
    )
    print(create_result_flex)

    print("----- get request (flex) -----")
    get_result_flex = client.content_generation.tasks.get(create_result_flex.id)
    print(get_result_flex)
    print("Flex ServiceTier:", getattr(get_result_flex, "service_tier", None))
    print("Flex ExecutionExpiresAfter:", getattr(get_result_flex, "execution_expires_after", None))

    print("----- list request (flex) -----")
    list_result_flex = client.content_generation.tasks.list(
        page_num=1,
        page_size=10,
        service_tier="flex",
    )
    print(list_result_flex)
    if list_result_flex.items:
        print("Flex List Item ServiceTier:", getattr(list_result_flex.items[0], "service_tier", None))
        print(
            "Flex List Item ExecutionExpiresAfter:", getattr(list_result_flex.items[0], "execution_expires_after", None)
        )

    print("----- delete request (flex) -----")
    try:
        client.content_generation.tasks.delete(create_result_flex.id)
        print(create_result_flex.id)
    except Exception as e:
        print(f"failed to delete flex task: {e}")
