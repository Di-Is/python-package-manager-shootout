# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "tomli-w",
# ]
# ///
import re

import tomli_w
import tomllib

pyproject = "pyproject.toml"

# 依存関係を解析する正規表現
pattern = re.compile(r"^([a-zA-Z0-9._-]+)(?:\[(.*)\])?(==|>=|<=|~=|!=|<|>)?([\d.]+)?$")

# requirements.txt の内容を読み込み、フィルタリング
with open("requirements.txt", "r") as f:
    lines = f.read().splitlines()

# パッケージとバージョンを抽出し、辞書形式に変換
deps = {}
for line in lines:
    line = line.strip()
    if not line or line.startswith("#"):  # 空行とコメント行を除外
        continue
    match = pattern.match(line)
    if match:
        name = match.group(1)
        extras = match.group(2)  # extras 部分
        operator = match.group(3) or ""
        version = match.group(4) or "*"
        # extras がある場合は特殊形式にする
        if extras:
            deps[name] = {
                "version": operator + version if operator else version,
                "extras": [e.strip() for e in extras.split(",")],
            }
        else:
            deps[name] = operator + version if operator else version

# pyproject.toml を読み込み
with open(pyproject, "rb") as f:
    py = tomllib.load(f)

# 依存関係を更新
py["tool"]["poetry"]["dependencies"].update(deps)

# 更新内容を書き戻し
with open(pyproject, "wb") as f:
    tomli_w.dump(py, f)
