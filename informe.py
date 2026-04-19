#!/usr/bin/env python3
"""TokenGuard Informe — Analiza logs de Claude Code y genera un dashboard.

Lee los logs JSONL locales de ~/.claude/projects/.
Cero llamadas a la API. Cero coste en tokens. Solo lectura de disco.

Uso:
    python informe.py                  # Todos los proyectos, últimas 10 sesiones
    python informe.py --sessions 20    # Últimas 20 sesiones
    python informe.py --project foo    # Solo proyectos que coincidan con 'foo'
    python informe.py --pro            # Desbloquear secciones Pro (requiere licencia)
"""

import json
import os
import sys
import argparse
import html
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

# ─── Config ───

CLAUDE_DIR = Path.home() / ".claude" / "projects"
TEMPLATE_DIR = Path(__file__).parent
TOKENS_PER_CHAR = 0.25  # ~4 chars per token (conservative estimate)
DUPLICATE_WINDOW_SECONDS = 300  # Same file read within 5 min = duplicate

# ─── Log Parsing ───

def find_sessions(project_filter=None, max_sessions=10):
    """Find JSONL session files, optionally filtered by project name."""
    sessions = []
    if not CLAUDE_DIR.exists():
        return sessions

    for project_dir in CLAUDE_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        if project_filter and project_filter.lower() not in project_dir.name.lower():
            continue

        for jsonl_file in project_dir.glob("*.jsonl"):
            sessions.append({
                "path": jsonl_file,
                "project": project_dir.name,
                "mtime": jsonl_file.stat().st_mtime,
            })

    sessions.sort(key=lambda s: s["mtime"], reverse=True)
    return sessions[:max_sessions]


def parse_session(session_path):
    """Parse a single JSONL session file and extract metrics."""
    tool_calls = []
    token_usage = []
    timestamps = []
    tool_results = {}

    with open(session_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")
            message = entry.get("message", {})
            role = message.get("role", "")
            timestamp = entry.get("timestamp", "")

            if timestamp:
                timestamps.append(timestamp)

            # Extract tool calls from assistant messages
            if role == "assistant" and isinstance(message.get("content"), list):
                for block in message["content"]:
                    if block.get("type") == "tool_use":
                        tool_calls.append({
                            "name": block.get("name", ""),
                            "input": block.get("input", {}),
                            "id": block.get("id", ""),
                            "timestamp": timestamp,
                        })

                # Extract token usage
                usage = message.get("usage", {})
                if usage:
                    token_usage.append({
                        "input": usage.get("input_tokens", 0),
                        "output": usage.get("output_tokens", 0),
                        "cache_read": usage.get("cache_read_input_tokens", 0),
                        "cache_creation": usage.get("cache_creation_input_tokens", 0),
                    })

            # Extract tool result sizes
            if role == "user" and isinstance(message.get("content"), list):
                for block in message["content"]:
                    if block.get("type") == "tool_result":
                        content = block.get("content", "")
                        if isinstance(content, str):
                            tool_results[block.get("tool_use_id", "")] = len(content)

    return tool_calls, token_usage, timestamps, tool_results


def analyze_session(session_info):
    """Analyze a single session and return structured metrics."""
    tool_calls, token_usage, timestamps, tool_results = parse_session(session_info["path"])

    if not tool_calls:
        return None

    # Tool call counts
    tool_counts = Counter(tc["name"] for tc in tool_calls)

    # Read analysis
    reads = [tc for tc in tool_calls if tc["name"] == "Read"]
    read_files = [tc["input"].get("file_path", "") for tc in reads]
    read_counts = Counter(read_files)
    duplicated_reads = {f: c for f, c in read_counts.items() if c > 1}
    total_reads = len(reads)
    unique_reads = len(read_counts)
    duplicate_read_count = sum(c - 1 for c in read_counts.values() if c > 1)

    # Estimate tokens wasted on duplicate reads
    tokens_wasted = 0
    for tc in tool_calls:
        if tc["name"] == "Read":
            file_path = tc["input"].get("file_path", "")
            if read_counts.get(file_path, 0) > 1:
                result_size = tool_results.get(tc["id"], 0)
                tokens_wasted += int(result_size * TOKENS_PER_CHAR)

    # Subtract first read of each duplicated file (that one is useful)
    for file_path, count in duplicated_reads.items():
        first_tc = next(tc for tc in tool_calls if tc["name"] == "Read" and tc["input"].get("file_path") == file_path)
        first_size = tool_results.get(first_tc["id"], 0)
        tokens_wasted -= int(first_size * TOKENS_PER_CHAR)

    # Token totals
    total_input = sum(u["input"] for u in token_usage)
    total_output = sum(u["output"] for u in token_usage)
    total_cache_read = sum(u["cache_read"] for u in token_usage)
    total_cache_creation = sum(u["cache_creation"] for u in token_usage)

    # Duration
    duration_min = 0
    if len(timestamps) >= 2:
        try:
            t_start = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00"))
            t_end = datetime.fromisoformat(timestamps[-1].replace("Z", "+00:00"))
            duration_min = round((t_end - t_start).total_seconds() / 60, 1)
        except (ValueError, TypeError):
            pass

    # Session date
    session_date = ""
    if timestamps:
        try:
            session_date = datetime.fromisoformat(timestamps[0].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            pass

    # Efficiency ratio
    efficiency = 0
    if total_reads > 0:
        efficiency = round((1 - duplicate_read_count / total_reads) * 100, 1)

    return {
        "session_id": session_info["path"].stem[:8],
        "project": session_info["project"],
        "date": session_date,
        "duration_min": duration_min,
        "tool_counts": dict(tool_counts),
        "total_tool_calls": len(tool_calls),
        "total_reads": total_reads,
        "unique_reads": unique_reads,
        "duplicate_reads": duplicate_read_count,
        "duplicated_files": {os.path.basename(f): c for f, c in duplicated_reads.items()},
        "tokens_wasted_estimate": tokens_wasted,
        "efficiency_ratio": efficiency,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cache_read": total_cache_read,
        "total_cache_creation": total_cache_creation,
        "top_reread_files": [
            {"file": os.path.basename(f), "count": c}
            for f, c in sorted(duplicated_reads.items(), key=lambda x: x[1], reverse=True)[:5]
        ],
    }


# ─── Aggregation ───

def aggregate(sessions_data):
    """Aggregate metrics across sessions."""
    total_reads = sum(s["total_reads"] for s in sessions_data)
    total_duplicates = sum(s["duplicate_reads"] for s in sessions_data)
    total_wasted = sum(s["tokens_wasted_estimate"] for s in sessions_data)
    total_tool_calls = sum(s["total_tool_calls"] for s in sessions_data)
    total_output = sum(s["total_output_tokens"] for s in sessions_data)

    # Top reread files across all sessions
    all_rereads = Counter()
    for s in sessions_data:
        for f, c in s.get("duplicated_files", {}).items():
            all_rereads[f] += c

    # Efficiency over time
    efficiency_history = [
        {"session": s["session_id"], "date": s["date"], "ratio": s["efficiency_ratio"]}
        for s in sessions_data
    ]

    # Tool distribution
    tool_totals = Counter()
    for s in sessions_data:
        tool_totals.update(s["tool_counts"])

    # Streak (consecutive sessions with >80% efficiency)
    streak = 0
    for s in reversed(sessions_data):
        if s["efficiency_ratio"] >= 80:
            streak += 1
        else:
            break

    avg_efficiency = round(sum(s["efficiency_ratio"] for s in sessions_data) / len(sessions_data), 1) if sessions_data else 0

    return {
        "session_count": len(sessions_data),
        "total_reads": total_reads,
        "total_duplicates": total_duplicates,
        "total_wasted_tokens": total_wasted,
        "total_tool_calls": total_tool_calls,
        "total_output_tokens": total_output,
        "avg_efficiency": avg_efficiency,
        "streak": streak,
        "top_reread_files": [
            {"file": f, "count": c}
            for f, c in all_rereads.most_common(10)
        ],
        "efficiency_history": efficiency_history,
        "tool_distribution": dict(tool_totals),
        "sessions": sessions_data,
    }


# ─── Dashboard Generation ───

def generate_dashboard(data, is_pro=False):
    """Generate HTML dashboard from aggregated data."""
    template_path = TEMPLATE_DIR / "template-report.html"

    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        print(f"Template not found at {template_path}, using inline template.")
        template = get_inline_template()

    # Inject data as JSON
    data_json = json.dumps(data, ensure_ascii=False, indent=2)
    output = template.replace("/*__DATA__*/", f"const REPORT_DATA = {data_json};")
    output = output.replace("/*__IS_PRO__*/", f"const IS_PRO = {'true' if is_pro else 'false'};")

    return output


def get_inline_template():
    """Fallback inline template if template.html is missing."""
    return """<!DOCTYPE html><html><head><title>TokenGuard Report</title></head>
<body><pre>Template not found. Run from the TokenGuard directory.</pre></body></html>"""


# ─── Main ───

def main():
    parser = argparse.ArgumentParser(description="TokenGuard Report — Claude Code log analyzer")
    parser.add_argument("--sessions", type=int, default=10, help="Número de sesiones recientes a analizar")
    parser.add_argument("--project", type=str, default=None, help="Filtrar por nombre de proyecto")
    parser.add_argument("--pro", action="store_true", help="Activar secciones Pro")
    parser.add_argument("--output", type=str, default=None, help="Ruta del archivo de salida (por defecto: reports/report-YYYY-MM-DD_HH-MM.html)")
    args = parser.parse_args()

    print("TokenGuard Informe v1.0")
    print(f"Escaneando {CLAUDE_DIR}...")

    sessions = find_sessions(project_filter=args.project, max_sessions=args.sessions)

    sessions_data = []
    if sessions:
        print(f"{len(sessions)} sesión(es) encontrada(s). Analizando...")
        for s in sessions:
            result = analyze_session(s)
            if result:
                sessions_data.append(result)

    data = aggregate(sessions_data)
    dashboard_html = generate_dashboard(data, is_pro=args.pro)

    # Generate into reports/ with date
    if args.output:
        output_path = args.output
    else:
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        output_path = str(reports_dir / f"report-{date_str}.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dashboard_html)

    print(f"\nInforme generado: {output_path}")
    if sessions_data:
        print(f"Sesiones analizadas: {data['session_count']}")
        print(f"Eficiencia media: {data['avg_efficiency']}%")
        print(f"Tokens desperdiciados (estimado): {data['total_wasted_tokens']:,}")
    else:
        print("No se encontraron sesiones con datos. El informe mostrará estado de bienvenida.")
        print("Usa Claude Code durante unas sesiones y vuelve a ejecutar este informe.")
    print(f"\nAbre {output_path} en tu navegador para ver el informe.")


if __name__ == "__main__":
    main()
