"""Structured output example: client.beta.chat.completions.parse with a Pydantic model.

The typed ``parse()`` shortcut converts the model class to a JSON Schema,
sends it as ``response_format`` to /chat/completions, then deserialises the
response back into the model via ``choice.message.parsed``.

For tool calls, see ``pydantic_function_tool`` for the same trick over
``tool_call.function.parsed_arguments``.
"""

import os
from typing import List

from pydantic import BaseModel

from arkruntime import Ark

# Authentication
# 1.If you authorize your endpoint using an API key, you can set your api key to environment variable "ARK_API_KEY"
client = Ark()
MODEL = os.environ.get("ENDPOINT_ID", "doubao-seed-2-1-pro-260628")


class MeetingInfo(BaseModel):
    time: str
    participants: List[str]


if __name__ == "__main__":
    print("----- standard request -----")
    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {"role": "system", "content": "提取会议信息"},
            {"role": "user", "content": "周三下午3点产品组会议，参加人员：张三、李四"},
        ],
        response_format=MeetingInfo,
    )

    meeting = completion.choices[0].message.parsed
    assert meeting is not None  # populated by parse() when response_format is a model
    print(f"会议时间：{meeting.time}")
    print(f"参会人员：{meeting.participants}")
