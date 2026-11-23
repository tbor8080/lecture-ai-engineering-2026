# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：1. search_materials / 2. glossary_search_glossary
- STEP 2 の [tool call]：glossary_search_glossary({'query': '3レベル'})
- STEP 3 の [tool call]：fetch_fetch({'url': 'https://modelcontextprotocol.io/'})
- STEP 4 の [tool call]：aws_aws___search_documentation({'search_phrase': 'Amazon S3 versioning overview', 'topics': ['general']})
- 気づき・疑問：
	- Step1,2は、以前の講義で確認済だったので、変化は感じませんでした。
	- Step3から、サーバーとのやり取りに切り替わる変化を確認できました。
	- Step4では、AgentがAWSに接続してツールを取得・利用していることがわかりました。

## 宿題
<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->
- 取り組んだレベル：基礎
- やったこと： `app/mcp_server.py`に`server.tool()(tools.get_lecture_summary)`を追加しました.
- 結果：
	1. ツールが`mcp_server.py`に追加されたことを確認しました。
	2. `--list-tools`で8つに増えたことを確認しました。（演習時点では,7つでした。）
	3. `app.mcp_agent --trace "質問内容"`において、get_lecture_summaryが、traceに示されたのを確認しました。
	4. 最後に、`pytest`を実行し、テストが全て通るのを確認しました。
#### 実行結果: `app.mcp_agent --list-tools`
	```Shell
	# 結果: 
	[server] glossary: コマンドで起動（uv run python -m ...
	モデルに見えているツール: 8 個
	...

	[glossary_get_lecture_summary]
	...
	# aws: 長かったので、抜粋
	...
	```

#### 質問: `第2回では何を学びますか？`
	```Shell
	...
	--- trace ---
	[tool call]   glossary_get_lecture_summary({'lecture': 2})
	[tool return] glossary_get_lecture_summary -> # 第2回 ファイン…(省略)
	[usage] 入力 5,942 tokens / 出力 242 tokens / モデル応答 2 回
	```
#### `pytest`
	```shell
	21 passed in 2.31s
	```

- 気づき・疑問：
	- 設定ファイルにサーバーを記述するだけで外部とのやりとりが意外と簡単にできることが面白かった。
	- ツールもエージェントのツールの追加とさほど変わらず、難しく感じなかった。
	- セキュリティ面や信頼性については、外部ツールが何を行っているかを考慮し、信頼性のないものは安易に利用しないのが良いと感じました。
	- MCPを使った開発では、外部サーバーの利点が、コンピューターとの依存がない点だったが、問題が起こった際の原因究明は根拠を見つけないと難しいと感じました。

---
- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
