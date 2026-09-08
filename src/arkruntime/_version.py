# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import re
from importlib.metadata import version
from pathlib import Path


def _get_version() -> str:
    # Source and editable imports must use this checkout, even if another
    # arkruntime distribution is installed. Releases use wheel metadata,
    # which setuptools derives from the same pyproject.toml project.version.
    source_root = Path(__file__).resolve().parent.parent
    pyproject = source_root.parent / "pyproject.toml"
    if source_root.name == "src" and pyproject.is_file():
        # The project declares a static, single-line version. Read only the
        # [project] table without requiring a TOML dependency on Python 3.8.
        project = re.search(r"(?ms)^\[project\][ \t]*\n(.*?)(?=^\[|\Z)", pyproject.read_text(encoding="utf-8"))
        if project is not None:
            declared = re.search(r"""(?m)^version\s*=\s*["']([^"'\r\n]+)["'][ \t]*(?:#.*)?$""", project[1])
            if declared is not None:
                return declared[1]
        raise RuntimeError("Expected a static project.version in " + str(pyproject))
    return version("arkruntime")


VERSION = _get_version()
