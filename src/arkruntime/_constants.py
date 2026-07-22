# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

import httpx

VERSION = "1.0.0"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


# Cloud presets. ``ARK_API_KEY`` is shared across clouds; AK/SK env-var names
# differ. Use ``Ark.volc(...)`` / ``Ark.byteplus(...)`` to pick a preset.
class Cloud(str):
    VOLC = "volc"
    BYTEPLUS = "byteplus"


_CLOUD_PRESETS = {
    Cloud.VOLC: {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "region": "cn-beijing",
        "ak_env": "VOLC_ACCESSKEY",
        "sk_env": "VOLC_SECRETKEY",
    },
    Cloud.BYTEPLUS: {
        "base_url": "https://ark.ap-southeast.bytepluses.com/api/v3",
        "region": "ap-southeast-1",
        "ak_env": "BYTEPLUS_ACCESSKEY",
        "sk_env": "BYTEPLUS_SECRETKEY",
    },
}

RAW_RESPONSE_HEADER = "X-Stainless-Raw-Response"
CLIENT_REQUEST_HEADER = "X-Client-Request-Id"
SERVER_REQUEST_HEADER = "X-Request-Id"
ARK_E2E_ENCRYPTION_HEADER = "x-is-encrypted"
ARK_APIKEY_PROJECT_NAME = "X-Project-Name"

DEFAULT_TIMEOUT_SECONDS = 600.0
DEFAULT_CONNECT_TIMEOUT_SECONDS = 60.0
# default timeout is 1 minutes
DEFAULT_TIMEOUT = httpx.Timeout(timeout=DEFAULT_TIMEOUT_SECONDS, connect=DEFAULT_CONNECT_TIMEOUT_SECONDS)

DEFAULT_MAX_RETRIES = 2
DEFAULT_CONNECTION_LIMITS = httpx.Limits(max_connections=1000, max_keepalive_connections=100)

INITIAL_RETRY_DELAY = 0.5
MAX_RETRY_DELAY = 8.0

_DEFAULT_MANDATORY_REFRESH_TIMEOUT = 10 * 60  # 10 min
_DEFAULT_ADVISORY_REFRESH_TIMEOUT = 30 * 60  # 30 min
_DEFAULT_STS_TIMEOUT = 7 * 24 * 60 * 60  # 7 days

_DEFAULT_RESOURCE_TYPE = "endpoint"
_PRESETENDPOINT_RESOURCE_TYPE = "presetendpoint"
