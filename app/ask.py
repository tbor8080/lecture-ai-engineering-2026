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

# from app.config import MODEL, api_error_message, get_api_key
from app.config import MODEL, TEMPERATURE, api_error_message, get_api_key

# 応答時間計測のため、time
import time
# 
from google.genai import types

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"

# 質問の回答と、入力トークン数、出力トークン数を返す
def ask(question: str) -> tuple[str, int | None, int | None]:
    client = genai.Client(api_key=get_api_key())
    # response = client.models.generate_content(model=MODEL, contents=question)
    response = client.models.generate_content(model=MODEL, contents=question, config=types.GenerateContentConfig(temperature=TEMPERATURE))

    input_tokens, output_tokens = get_token(response)
    return response.text, input_tokens, output_tokens

# Token取得。response.usage_metadataがNoneの場合もある。usageがNoneのとき、そのまま返す
def get_token(response) -> tuple[int | None, int | None]:
    usage = response.usage_metadata
    if usage is None:
        return None, None
    return usage.prompt_token_count, usage.candidates_token_count

def main() -> None:
		# コマンドラインの引数の入力をinput関数に変更。
		# parser = argparse.ArgumentParser(description="素のLLMに質問する")
		# parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
		# args = parser.parse_args()
		# 質問の履歴を保持するリスト（メモリ上）
		histories = []
		# 無料枠のトークン数も考慮、たくさんの履歴を保持しない。
		max_histories = 2
		print(f"[model] {MODEL}")
		print(f"対話モードを開始します...")
		print("終了: quit -> Enter")
		# 課題2:
		while True:
				try:
						# テキスト整形
						raw_input = input("[⚫︎質問を入力してください] > ")
						# 簡易入力チェック

						if raw_input.lower() == "quit":
								print("会話を終了します。")
								break
						elif raw_input.strip() == "":
								print("空の質問です。何か入力を行なってください。")
								raw_input = DEFAULT_QUESTION
								# continue
						raw_input = f"[質問] :{raw_input}"
						print(f"{raw_input}\n")
						input_question = f"以下の質問に100文字程度で答えてください。\n{raw_input}"
						# 質問の履歴をまとめて送信することで、過去の質問を踏まえた回答が得られる。token数が増えるので、プロンプトに解答の制約を追記。
						history_tmp = [f" {q}\n{a}" for q, a, _, _, _ in histories]
						history_tmp.append(input_question)
						input_question = "\n".join(history_tmp)
						# 計測開始
						start = time.time()
						# 質問の返信(Gemini)
						result, input_tokens, output_tokens = ask(input_question)
						end = time.time()
						# 計測終了
						# 出力
						# 応答時間表示
						elapsed_time = ask_time_view(start, end)
						# 最新の質問に対する回答を更新
						# result = f"[回答] :{result}"
						result_tmp = f"[回答] :{result}"
						histories.append((raw_input, result_tmp, input_tokens, output_tokens, elapsed_time))
						# 履歴はmax_historiesで管理
						if len(histories) > max_histories:
								# 質問の履歴を{max_questions}件までに制限
								histories.pop(0)
						# 返答・過去の質問・token数表示
						result_view(result, histories, input_tokens, output_tokens)
						# 区切り
						print("次の質問を入力してください。")
				except errors.APIError as e:
						print(api_error_message(e.code, e.message))
						raise SystemExit(1)

# 返答表示：課題2
def result_view(result:str, histories:list, input_tokens:int, output_tokens:int)->None:
		border_length = 64
		print(result)
		print(f"[トークン使用量] {input_tokens} (入力), {output_tokens} (出力)")
		# 履歴
		for i in range(len(histories)):
				print("-" * border_length)
				print(f"[履歴({i+1})|TIME:{histories[i][4]:.2f} sec. | TOKEN > Q:{histories[i][2]} Token / A:{histories[i][3]} Token]\n{histories[i][0]}\n{histories[i][1]}\n{i+1}はここまで\n")
		print("*" * border_length)
# 応答時間表示(sec)：課題3
def ask_time_view(start:float, end:float)->None:
		border_length = 64
		t = end - start
		print("="*border_length)
		print(f"\n[応答時間] : {t:.2f} sec.")
		print("="*border_length)
		return t

if __name__ == "__main__":
		main()