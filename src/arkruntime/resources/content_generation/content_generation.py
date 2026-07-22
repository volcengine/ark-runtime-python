# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from ..._compat import cached_property
from ..._resource import AsyncAPIResource, SyncAPIResource
from .tasks import AsyncTasks, Tasks


class ContentGeneration(SyncAPIResource):
    @cached_property
    def tasks(self) -> Tasks:
        return Tasks(self._client)


class AsyncContentGeneration(AsyncAPIResource):
    @cached_property
    def tasks(self) -> AsyncTasks:
        return AsyncTasks(self._client)
