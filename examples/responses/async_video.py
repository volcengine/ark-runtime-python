"""Upload a video, wait for preprocessing, then run a 2-turn Responses session
referencing the uploaded file_id.

Demonstrates:
- `client.files.create(file=..., purpose=..., preprocess_configs={"video": {"fps": ...}})`
- `client.files.wait_for_processing(file_id)` for the active/failed terminal state
- `client.responses.create(input=[..., {"type": "input_video", "file_id": ...}])`
  with caching + previous_response_id for multi-turn
"""

import asyncio
import sys
from pathlib import Path

from arkruntime import AsyncArk
from arkruntime.types.responses import ResponseCompletedEvent

client = AsyncArk()


DEFAULT_VIDEO_URL = "https://an-test-imgs.tos-cn-beijing.volces.com/videos/test_videos/04_duration_5s.mp4"


async def main() -> None:
    if len(sys.argv) > 1:
        video_path = Path(sys.argv[1])
        if not video_path.exists():
            sys.exit(f"video file '{video_path}' not found")
    else:
        # No local file supplied — fall back to a small public sample so the
        # example is runnable out of the box.
        import urllib.request

        video_path = Path("ark_vlm_video_input.mp4")
        if not video_path.exists():
            print(f"Downloading sample video from {DEFAULT_VIDEO_URL}")
            urllib.request.urlretrieve(DEFAULT_VIDEO_URL, video_path)

    print(f"Uploading {video_path}")
    with video_path.open("rb") as video_file:
        file = await client.files.create(
            file=video_file,
            purpose="user_data",
            preprocess_configs={
                "video": {
                    "fps": 0.3,  # sampling fps; default is 1.0
                }
            },
        )
    print(f"  uploaded id={file.id} status={file.status}")

    file = await client.files.wait_for_processing(file.id)
    print(f"  processed status={file.status}")
    if file.status != "active":
        sys.exit(f"file {file.id} did not become active: status={file.status}")

    file_id = file.id

    # ==========================================================
    # Turn 1: multi-modal input + caching enabled
    # ==========================================================
    print("\nTurn 1: ask the model to analyze the video frame-by-frame")
    stream = await client.responses.create(
        model="doubao-seed-2-1-pro-260628",
        input=[
            {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
            {
                "role": "user",
                "content": [
                    {"type": "input_video", "file_id": file_id},
                    {"type": "input_text", "text": "请逐帧分析视频内容"},
                ],
            },
        ],
        caching={"type": "enabled"},
        store=True,
        stream=True,
    )
    response_id = ""
    async for event in stream:
        print(event)
        if isinstance(event, ResponseCompletedEvent):
            response_id = event.response.id

    # ==========================================================
    # Turn 2: continue via previous_response_id
    # ==========================================================
    print("\nTurn 2: follow-up referencing prior turn's response")
    stream = await client.responses.create(
        model="doubao-seed-2-1-pro-260628",
        previous_response_id=response_id,
        input=[
            {"role": "user", "content": "上一轮对话里视频里的内容是"},
        ],
        caching={"type": "enabled"},
        store=True,
        stream=True,
    )
    async for event in stream:
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
