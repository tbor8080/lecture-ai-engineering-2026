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
- 取り組んだレベル：基礎 / 実装 / 発展
- やったこと：
- 結果：
- 気づき・疑問：
