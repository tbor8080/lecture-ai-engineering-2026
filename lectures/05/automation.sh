#!/usr/bin/env bash
# デフォルト: sh automation.sh default "コンパクションを使う場面は？" 1
# 情報追加: sh automation.sh plus_context "コンパクションを使う場面は？" 1
# 実行ログ: /workspaces/lecture-ai-engineering-2026/lectures/05/logs/retrieval.jsonl
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "エラー: 引数は3つ指定してください（パターン 質問 回数）" >&2
  echo "例: $0 default \"コンパクションを使う場面は？\" 1" >&2
  exit 1
fi

PATTERN="${1:-default}"          # 例: default / plus_context
QUERY="${2:-'コンパクションを使う場面は？'}"
COUNT="${3:-5}"                  # 実行回数
SLEEP_SEC="12"             # 通常時の実行間待機秒数（毎分5回目安: 12、毎分10回目安: 8〜10）
MAX_RETRIES="3"            # 429時の最大リトライ回数
RETRY_WAIT_SEC="10"        # 初回リトライ待機秒数

# OUT_DIR="./logs/auto"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/logs/auto"
LOG_FILE="${OUT_DIR}/agent-$(date +%Y-%m-%d_%H%M%S).log" # -$(date +%Y-%m-%d_%H%M%S)
mkdir -p "$OUT_DIR"

is_rate_limit_error() {
  local text="$1"
  printf '%s\n' "$text" | grep -qiE '(429|RESOURCE_EXHAUSTED|rate[[:space:]]*-?limit|too[[:space:]]+many[[:space:]]+requests|quota)'
}

run_agent_with_retry() {
	local attempt=0
	local wait_sec="$RETRY_WAIT_SEC"
	local tmp_out exit_code raw
	
	while true; do
		tmp_out=$(mktemp)
		set +e
		
		if [ "${PATTERN}" = "plus_context" ]; then
			RAG_PLUS_CONTEXT=1 uv run python -m app.agent "${QUERY}" --trace 2>&1 | tee "$tmp_out"
		else
			run python -m app.agent "${QUERY}" --trace 2>&1 | tee "$tmp_out"
		fi
	
		exit_code=${PIPESTATUS[0]}

		set -e

		raw=$(cat "$tmp_out")
		rm -f "$tmp_out"

		if [ "$exit_code" -eq 0 ]; then
			printf '%s' "$raw"
			return 0
		fi

		if is_rate_limit_error "${raw}" && [ "${attempt}" -lt "${MAX_RETRIES}" ]; then
			attempt=$((attempt + 1))
			echo "[WARN] 429/レート制限を検知しました（リトライ ${attempt}/${MAX_RETRIES}）。${wait_sec}秒待機します..." >&2
			sleep "${wait_sec}"
			wait_sec=$((wait_sec + 15))
			continue
		fi

		echo "[ERROR] 実行に失敗しました（終了コード: ${exit_code}、リトライ回数: ${attempt}/${MAX_RETRIES}）。" >&2
		printf '%s' "${raw}"
		return "${exit_code}"
	done
}

for i in $(seq 1 "$COUNT"); do
	TS=$(date -Iseconds)
	echo "[${i}/${COUNT}] (${PATTERN}) 実行中... (${TS})"

	RAW=$(run_agent_with_retry)

	{
	echo "============================================================"
	echo "timestamp: ${TS} | pattern: ${PATTERN} | run: ${i}/${COUNT} | query: ${QUERY}"
	echo "============================================================"
	echo "${RAW}"
	echo ""
	} >> "${LOG_FILE}"

	if [ "${i}" -lt "${COUNT}" ]; then
		sleep "${SLEEP_SEC}"
	fi
done

echo "完了: $LOG_FILE に保存しました。"