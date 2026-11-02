# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
#### [LLM]
```markdown
AIE2026の講座における「3レベル」とは、生成AIを活用する際の習熟度や段階（例えば、基礎・応用・実践など）を示す指標です。自身のスキルや目的に合わせ、段階的に学習を進めるための基準として設定されています。
```  
#### [agent]
```markdown
[model] gemini-3.5-flash-lite
「3レベル」とは、AIE2026の宿題の構成を示す言葉で、以下の3つの段階に分かれています。

1. **基礎**：講義内容の確認
2. **実装**：自分でコードを書く
3. **発展**：調査や試行

この3つのレベルのうち**どれか1つ**に取り組めば、その回の宿題は完了となります（原則として採点は行いません）。ご自身の理解度や目的に合わせて、取り組むレベルを選んでみてくださいね。

関連する回：第1回
```  

---
- `--trace` で見えたツール呼び出し（ツール名と引数）：
```markdown
$ uv run python -m app.agent --trace "LoRAとQLoRAの違いは？"
--- 
[agentからの出力]
[model] gemini-3.5-flash-lite
講座の用語集によると、LoRAとQLoRAの違いは以下のとおりです。

* **LoRA**
  事前学習済みの重みを固定したまま、重みの更新分を2つの小さな低ランク行列の積で表し、その小さな行列だけを学習するPEFT（Parameter-Efficient Fine-Tuning）手法です。学習パラメータや保存ファイルを少なく抑えられます。
* **QLoRA**
  ベースモデルの重みを4ビットなどに量子化（Quantization）してメモリを大きく節約したうえで、LoRAによる学習を行う手法です。これにより、より大きなモデルを小さなGPU環境でも扱えるようになります。

関係する回：第2回

--- trace ---
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, "definition": "事前学習済みの重みは固定したまま、重みの更新分を2つの小さな行列の積（低ランク行列）で表し、その小さな行列だけを学習するPEFT手法。学習するパラ…
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, "definition": "ベースモデルの重みを4ビットなどに量子化してメモリを節約したうえで、LoRAで学習する手法。より大きなモデルを小さなGPUで扱える。本講座の第2…
[usage] RunUsage(cost=Decimal('0.0008213'), details={'text_prompt_tokens': 1196}, input_text_tokens=1196, input_tokens=1196, output_tokens=185, requests=2, tool_calls=2)
```  
- 1つの質問での LLM 呼び出し回数（`requests`）：2
- 追加したツールと、docstring に書いた説明：

## 宿題

- 取り組んだレベル：基礎
- やったこと：
- 結果：
- 気づき・疑問：
---
- 取り組んだレベル：実装
- やったこと：
- 結果：
- 気づき・疑問：
---
- 取り組んだレベル：発展
- やったこと：
- 結果：
- 気づき・疑問：
