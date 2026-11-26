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

## 宿題1(基礎)
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

	[glossary_get_lecture_summary]
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
## 宿題2(実装)

- 取り組んだレベル：実装
- やったこと：
	- 以前に実装した`app/quiz.py`から`make_quiz`を`mcp_server.py`に追加しました。
	- 質問：第99回のクイズを作って
	- ファイル分割: `app/tools.py`から`app/quiz.py`に分割
- 結果：
	1. `mcp_agent`にツールとして登録されました。
	2. 「第99回のクイズを作って」と実行すると`glossary_make_quiz({'lecture': 99})`が呼ばれ、範囲外の場合は`{"error": "第99回は存在しません。"}`が返り、存在しない回であることを伝えられるようになった。
	3. `mcp_servers.json`の構成（接続サーバー数）によって入力トークン数が大きく変化した（5,665 tokens → 997 tokens）。
	#### 演習時の`mcp_servers.json`で実行
	```shell
	--- trace ---
	[tool call]   glossary_make_quiz({'lecture': 99})
	[tool return] glossary_make_quiz -> {"error": "第99回は存在しません。"}…
	[usage] 入力 5,665 tokens / 出力 83 tokens / モデル応答 2 回
	```
	#### `mcp_servers.json`から、awsなどの設定を削除して実行
	```shell
	--- trace ---
	[tool call]   glossary_make_quiz({'lecture': 99})
	[tool return] glossary_make_quiz -> {"error": "第99回は存在しません。"}…
	[usage] 入力 997 tokens / 出力 72 tokens / モデル応答 2 回
	```
- 気づき・疑問：
	1. 回答の表現や補足に揺れがあっても、存在しない回であることを否定できており意味は伝わる。違いそのものではなく意味の統一性を重視したいと感じた。
	2. `mcp_servers.json`にサーバーを追加・有効化すると、ツール定義などの影響で入力トークン数が増加することが確認できた。

--- 
## 宿題3(発展)
- 取り組んだレベル：発展
- やったこと：VS CodeのMCP設定について調べ、`app/mcp_servers.json`と比較した。
- 参照日付: 2026年11月26日
	- [Add and use MCP servers in VS Code](https://code.visualstudio.com/docs/agent-customization/mcp-servers)
- 結果：
	- 設定方法と置き場所
		1. コマンドパレット（`MCP: Add Server`）から `stdio`（例：`uv run python -m app.mcp_server`）や `URL`（例：`http://localhost:8888/mcp`）を選択して追加できる
		2. 設定ファイルとして、グローバル設定やプロジェクトルートの `.mcp.json` を直接編集することもできる
	- 起動・接続の例
		- コマンド（stdio）：`uvx`、`npx`など
		- URL：`https://learn.microsoft.com/api/mcp`(ローカルサーバも可能)など
	- 有効になる範囲
		1. グローバル（全体）
		2. リモート（開発コンテナ）
		3. ワークスペース（特定プロジェクト）

- 気づき・疑問：
	- `app/mcp_servers.json`はアプリ側でサーバーを指定する(`stdio`)のに対し、VS Codeではグローバル・コンテナ・ワークスペース環境のどこに適用するかを選んで設定できる点が便利だと感じた。
	- コマンドパレットから対話的に追加できるため、設定のハードルが低く使いやすかった。
	- 何をどの環境で実行するかを整理してから追加しないと構成が複雑になりそうだと感じた。
	- MCPサーバーを作成した時に、エージェントのハーネス側にどのような権限（ファイル操作や外部通信、環境変数など）まで渡すべきか、安全面の基準も気になった。