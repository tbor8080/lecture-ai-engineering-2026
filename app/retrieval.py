"""第5回: ページ単位のベクトル検索。"""

import argparse
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from collections import defaultdict, deque
from pathlib import Path

from google import genai
from google.genai import types
from pydantic_ai.exceptions import ModelHTTPError
import sqlite_vec

from app.config import (
    EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
    RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS,
)


def get_all_materials() -> str:
    """全資料を、講義・章・ページの情報付きで1つの文字列にまとめる。"""
    documents = json.loads(RAG_SOURCE.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"資料: {document['id']} / {document['title']}\n"
        f"章: {section['section']}\n"
        f"ページ: PDF p.{page['page']} / {page['title']}\n{page['content']}"
        for document in documents
        for section in document["content"]
        for page in section["content"]
    )

def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """資料→章→ページのJSONを、対象資料のページ一覧に変換する。"""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
    return pages


def browse_tree(node_id: str | None = None) -> dict:
    """直下のページは先頭文、指定したページ自身は全文を返す。"""
    tree = json.loads(RAG_TREE.read_text(encoding="utf-8"))
    tree["children"] = [node for node in tree["children"] if node["id"] in RAG_DOCUMENT_IDS]
    node_id = node_id or tree["id"]
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}

    def describe(node, full=False):
        info = {key: node[key] for key in ("id", "kind", "title")}
        if node["kind"] == "page":
            info.update({key: value for key, value in pages[node["id"]].items() if key != "page_id"})
            if not full:
                info["content"] = re.split(r"(?<=[。！？])|\n", info["content"].strip(), maxsplit=1)[0]
        return info

    remaining = [tree]
    while remaining:
        node = remaining.pop()
        if node["id"] == node_id:
            return {
                "node": describe(node, full=True),
                "children": [describe(child) for child in node.get("children", [])],
            }
        remaining.extend(node.get("children", []))
    raise ValueError("対象の目次ノードが見つかりません。")

def read_page(page_id: str) -> dict:
    """第1〜3回の本講義から、指定した1ページの本文と引用情報を返す。"""
    for page in load_pages(RAG_SOURCE):
        if page["page_id"] == page_id:
            return page
    raise ValueError("対象のページが見つかりません。")


def normalized_vector(values: list[float]) -> list[float]:
    """ベクトルの長さを1に揃える。"""
    norm = math.hypot(*values)
    if norm == 0:
        raise ValueError("埋め込みがゼロベクトルです。")
    return [value / norm for value in values]


def embed_text(text: str, task_type: str) -> list[float]:
    """Geminiで文章を埋め込む。入力上限を超えた場合は切り捨てず停止する。"""
    with genai.Client(api_key=get_api_key()) as client:
        count = client.models.count_tokens(model=EMBEDDING_MODEL, contents=text).total_tokens
        if count is None or count > EMBEDDING_MAX_TOKENS:
            raise ValueError(f"埋め込み入力が上限を超えるか計測不能です: {count} tokens。")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    embedding = response.embeddings[0]
    if embedding.statistics and embedding.statistics.truncated:
        raise ValueError("埋め込みAPIが本文を切り捨てました。")
    return normalized_vector(embedding.values)


@contextmanager
def open_index(path: Path):
    """既存の検索DBを読み取り専用で開き、終了時に閉じる。"""
    if not path.is_file():
        raise FileNotFoundError("検索DBがありません。")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        yield db
    finally:
        db.close()


def search(query: str) -> list[dict]:
    """質問を埋め込み、近いページを最大RAG_TOP_K件返す。"""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("検索語が空です。")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        rows = db.execute("""
            SELECT page_id, document_id, lecture, document_title, section, title, page, content,
                   vec_distance_cosine(embedding, ?) AS distance
            FROM chunks ORDER BY distance, page_id LIMIT ?
        """, (sqlite_vec.serialize_float32(vector), RAG_TOP_K))
        # return [dict(row) for row in rows]
        # 実装: LLMに渡す情報を前後ページまで渡すかどうか
        import time
        timer = time.perf_counter()
        results = [dict(row) for row in rows]
        seen = get_seen_keys(results)
        adjacent=[]
        for result in results:
            get_adjacent_context(result, seen)
            if result.get("prev"):
                adjacent.append(result.get("prev"))
            if result.get("after"):
                adjacent.append(result.get("after"))
        # ログに記録
        log_rag_run(caller_name(), RAG_PLUS_CONTEXT, len(results), len(adjacent), query.strip(), timer)
        return results

def search_graph(query: str) -> dict:
    """ベクトル検索を入口に、前後ページと共通用語で候補を広げる。"""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]
             if node["kind"] == "term" or node["id"] in pages}
    adjacent = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adjacent[a].add(b)
            adjacent[b].add(a)

    seeds = [hit for hit in search(query) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
    seed_ids = {seed["page_id"] for seed in seeds}
    results, candidates = [], {}
    for rank, seed in enumerate(seeds):
        root = seed["page_id"]
        results.append({**pages[root], "distance": seed["distance"], "hops": 0,
                        "path": [{"id": root, "title": pages[root]["title"]}]})
        queue = deque([(root, [root])])
        visited = {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= GRAPH_HOPS:
                continue
            # 同じ深さなら、接続先が少ない用語からたどる。
            neighbors = sorted(adjacent[current], key=lambda n: (len(adjacent[n]), n))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seed_ids:
                    continue
                frequency = max((len(adjacent[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                priority = (len(route) - 1, frequency, rank, neighbor)
                candidate = {**pages[neighbor], "hops": len(route) - 1,
                             "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
                if neighbor not in candidates or priority < candidates[neighbor][0]:
                    candidates[neighbor] = (priority, candidate)
    expanded = [candidate for _, candidate in sorted(candidates.values())]
    return {"seeds": results, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(results))],
            "max_hops": GRAPH_HOPS}

def run_full_context(agent, question: str, model, instructions: str, prompt_template: str):
    """全資料を一括投入し、検索ツールを使わずに回答する。"""
    prompt = prompt_template.format(materials=get_all_materials(), question=question)
    print(f"[full-context] 入力{len(prompt):,}文字")
    try:
        with agent.override(tools=[], instructions=instructions):
            return agent.run_sync(prompt, model=model)
    except ModelHTTPError as e:
        print(f"[full-context] APIエラー HTTP {e.status_code}: {e.body}")
        raise SystemExit(1)

# 実装: 単純に同じdoc_idと結果の前後ページを取得する
def search_page(doc_id: str, page: tuple[int, int]) -> list[dict]:
    pages = [p for p in page if p is not None and p >= 1]
    if not pages:
        return []
    """結果から同じdoc_idと結果の前後ページを取得する"""
    placeholders = ", ".join("?" for _ in pages)
    sql=f"""
        SELECT page_id, document_id, lecture, document_title, section, title, page, content
        FROM chunks 
        WHERE document_id = ? AND page IN ({placeholders})
    """
    with open_index(RAG_DB) as db:
        rows = db.execute(sql, (doc_id, *pages))
        return [dict(row) for row in rows]
# 実装
"""
app/retrieval.pyで、検索結果に前後1ページの本⽂も付けるよう改良します。
別の資料をまたがず、同じページが重複しないようにします。
通常の検索と⽐べ、根拠が増えた例と、不要な情報が増えた例を確認します。

LLMに渡されるのが、
"""
# RAG
def retrieval_query():
    parser = argparse.ArgumentParser(description="エージェントを使わず、講義資料の検索だけを実行する")
    parser.add_argument("query", help="調べたい内容")
    return parser.parse_args()

def get_seen_keys(results) -> set[tuple[str, int]]:
    return {(r["document_id"], r["page"]) for r in results}

from datetime import datetime
import time
import inspect

def caller_name() -> str:
    frame = inspect.currentframe()
    try:
        # _caller_name -> search -> 実際の呼び出し元
        caller = frame.f_back.f_back if frame and frame.f_back else None
        if caller is None:
            return "<unknown>"
        return f"{caller.f_code.co_name}:{caller.f_lineno}"
    finally:
        del frame

def log_rag_run(
    hook="search", 
    rag_plus_context=False, 
    result_count=0,
    adjacent_count=0,
    query="",
    timer=0
):
    """コンテキストログ保存"""
    
    LOG_PATH = Path(__file__).resolve().parent.parent / "lectures/05/logs/retrieval.jsonl"
    record = {
        "hook": hook,
        "rag_plus_context": rag_plus_context,
        "result_count": result_count,
        "adjacent_count": adjacent_count,
        "query": query,
        "time_ms": (time.perf_counter() - timer)*1000,
        "timestamp": datetime.now().strftime("%y-%m-%d %H:%M:%S"),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")

def is_rag_plus_context_enabled() -> bool:
    """UV_ENV_FILE=.env RAG_PLUS_CONTEXT=1 uv run python -m app.retrieval 'コンパクションを使う場面は？'"""
    import os
    plus_context = os.getenv("RAG_PLUS_CONTEXT")
    return plus_context is not None and plus_context.strip() != ""

RAG_PLUS_CONTEXT=is_rag_plus_context_enabled()

def get_adjacent_context(result: dict, seen: set[tuple[str, int]] | None = None)->list[dict]:
    """隣接するコンテキストに拡張"""
    if not RAG_PLUS_CONTEXT:
        return []
    contexts = search_page(result['document_id'], (result['page']-1, result['page']+1))
    if not contexts:
        return []
    prev, after = None, None
    adjacent: list[dict] = []
    for row in contexts:
        key = (row["document_id"], row["page"])
        if seen is not None and key in seen:
            continue
        if row['page'] < result['page']:
            prev = row
        elif row['page'] > result['page']:
            after = row
    result['prev'] = prev
    result['after'] = after
    return result

def print_adjacent_context(result, seen):
    prev = result.get("prev")
    after = result.get("after")
    if prev is not None:
        if seen is not None:
            seen.add((prev["document_id"], prev["page"]))
        print(f"前へ(P. {prev['page']}): {prev['title']}[{prev['document_title']}:{prev['section']}]")
        print(f"\n{prev['content']}")
    if after is not None:
        if seen is not None:
            seen.add((after["document_id"], after["page"]))
        # print("\n", "*"*32, "\n")
        print(f"次へ(P. {after['page']}): {after['title']}[{after['document_title']}:{after['section']}]", )
        print(f"\n{after['content']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="エージェントを使わず、講義資料の検索だけを実行する")
    parser.add_argument("query", help="調べたい内容")
    args = parser.parse_args()
    # 実装
    timer = time.perf_counter()
    results = list(search(args.query))
    # 重複ページを防ぐためのFlag
    seen = get_seen_keys(results)
    adjacent=[]
    for i, result in enumerate(results, 1):
        
        print(f"\n{'=' * 60}\n検索結果 {i}\n{'=' * 60}")
        print(f"講義: {result['document_title']}")
        print(f"章: {result['section']}")
        print(f"タイトル: {result['title']}")
        print(f"ページ: {result['page']}")
        print(f"\n{result['content']}")
        # 追記
        print_adjacent_context(result, seen)
    
        if result.get("prev"):
            adjacent.append(result.get("prev"))
        if result.get("after"):
            adjacent.append(result.get("after"))
        
    log_rag_run("main", RAG_PLUS_CONTEXT, len(results), len(adjacent), args.query, timer)