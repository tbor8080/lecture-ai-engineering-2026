"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

# 質問の回答と、入力トークン数、出力トークン数を返す
def ask(question: str) -> tuple[str, int | None, int | None]:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    input_tokens, output_tokens = get_token(response)
    return response.text, input_tokens, output_tokens

# tokenの取得。response.usage_metadataがNoneの場合もあるので、Noneを返すようにする
def get_token(response) -> tuple[int | None, int | None]:
    usage = response.usage_metadata
    if usage is None:
        return None, None
    return usage.prompt_token_count, usage.candidates_token_count
# 質問の履歴を保持するリスト（メモリ上）

histories = []
def main(input_question:str) -> None:
    # parser = argparse.ArgumentParser(description="素のLLMに質問する")
    # parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    # args = parser.parse_args()
    # 無料枠のトークン数も考慮して、多くの記憶を保持しないこと。
    max_histories = 2
    
    print(f"[model] {MODEL}")
    print(f"[質問] {input_question}\n")
    try:
        histories.append((None, None))
        if len(histories) > max_histories:
            histories.pop(0)  # 質問の履歴を{max_questions}件までに制限
        # 質問の履歴をまとめて送信することで、過去の質問を踏まえた回答が得られるが、token数が増えるので、履歴をまとめて送信するかどうかは要検討。(一旦は過去になる履歴に文字制限を設けて、まとめて送信する)
        input_question = "\n".join([q for q, _ in histories])  # 質問の履歴をまとめて送信
        result, input_tokens, output_tokens = ask(input_question)
        histories[-1] = (input_question, result[:150])  # 最新の質問に対する回答を更新

        print(f"[回答] {result}")
        print(f"[トークン使用量] {input_tokens} (入力), {output_tokens} (出力)")
        
        # 過去の質問の表示
        for i in range(len(histories)):
            print(f"[質問の履歴] {histories[i][0]} \n\n {histories[i][1]}")

    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)

if __name__ == "__main__":
    while(1):
        input_question = input("質問を入力してください（終了するには 'quit' と入力）: ")
        if input_question.lower() == 'quit':
            print("終了します。")
            break
        elif input_question.strip() == '':
            print("質問が空です。もう一度入力してください。")
            continue
        main(input_question)
