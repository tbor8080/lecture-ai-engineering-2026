"""第3回: エージェントに持たせるツール。

ここに書いた関数の docstring と型ヒントが、そのままモデルへの「ツールの説明文」になる。
説明文を書き換えると、モデルがツールを使うかどうか・どんな引数で呼ぶかが変わる。
"""

import json
from functools import cache
from pathlib import Path
# random.choice
import random

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """講座の用語集から用語を検索し、定義と、どの回で扱うかを返す。

    AIエンジニアリングの用語や、この講座（AIE2026）に固有の言葉について
    答える前に使うこと。query には調べたい用語を1つだけ入れる（例: "LoRA"）。
    """
    q = _normalize(query)
    if not q:
        return "検索語が空です。調べたい用語を1つ指定してください。"
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # 「r」のような短い別名が何にでも当たらないよう、名前側が短いものは除く
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"用語集に「{query}」は見つかりませんでした。"
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """指定した回（1始まりの整数）の講義の要点を返す。

    「第3回では何を学ぶ？」のように、回の内容や関係を聞かれたときに使う。
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"第{lecture}回の要点はまだありません。用意されている回: {', '.join(available)}"
    return path.read_text(encoding="utf-8")

def make_quiz(lecture: int) -> str:
    """ユーザーに「問題を出して」と頼まれた時に、指定された回の確認問題を用語集(glossary.json)内から出題する。
    
    call: make_quiz(2)
    return: {"question": "「PEFT」の意味は？", "answer": "モデルの全パラメータではなく、…"}
    """
    lectures = [lec for lec in load_glossary() if lec['lecture']==lecture]
    l = random.choice(lectures) if lectures else load_glossary()[0]
    return json.dumps(
        {
            "question": l['term'],
            "lecture": l['lecture'],
            "answer": l['definition']
        },
        ensure_ascii=False,
    )

# 課題:実装
from datetime import datetime
import os
def save_learning_log(lecture:int) -> str:
    """学習の記録をlearning_logフォルダに保存します。
    利用者の承認後、ログファイル(learning.json)の保存を行います。
    """
    #################################################################
    log_json = {"title": "学習記録", "dir":None, "file":None, "log":[]}
    log_file = "learning.json"
    path = Path("./lectures/03/learning_log")
    file = path / log_file
    log_json["dir"] = str(path)
    log_json["file"] = str(file)
    lectures = [lec for lec in load_glossary() if lec['lecture']==lecture]
    l = random.choice(lectures) if lectures else load_glossary()[0]

    if not path.is_dir():
        print(f"DIR: {path} Create.")
    path.mkdir(parents=True, exist_ok=True)
        
    # 更新用 dict
    update_json = {
        "lecture": lecture, 
        "term": l['term'],
        "definition": l['definition'],
        "date":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # fileが存在している場合。
    if file.is_file():
        with open(file, "r", encoding="utf-8") as fp:
            log_json["log"] = json.load(fp)["log"]

    # update log.
    log_json["log"].append(update_json)

    with open(file, "w", encoding="utf-8") as fp:
        json.dump(log_json, fp, ensure_ascii=False, indent=4)
    print(f"[save]: {file}を保存しました。")
    print(f"[latest json]: {log_json["log"][-1]}")
    # log json
    return json.dumps(log_json, ensure_ascii=False)