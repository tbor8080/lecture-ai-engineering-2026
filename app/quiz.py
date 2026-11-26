from app.tools import load_glossary
import random, json
# 第5回以前で実装したものを利用.(コンフリクトによる履歴の巻き戻り・agent.pyのINSTRUCTIONSも古いので第３回の指示を追加する必要があるかも。)
# ただし、編集は最小限にする.追跡しやすいように。
def make_quiz(lecture: int) -> str:
    """ユーザーに「問題を出して」と頼まれた時に、指定された回の確認問題を用語集(glossary.json)内から出題する。

    call: make_quiz(2)
    return: {"question": "「PEFT」の意味は？", "answer": "モデルの全パラメータではなく、…"}
    """
    lectures = [lec for lec in load_glossary() if lec['lecture']==lecture]
    # 該当回がなければ、Errorを返す。
    if not lectures:
        return json.dumps({"error": f"第{lecture}回は存在しません。"}, ensure_ascii=False)
    l = random.choice(lectures)
    return json.dumps(
        {
            "question": l['term'],
            "lecture": l['lecture'],
            "answer": l['definition']
        },
        ensure_ascii=False,
    )