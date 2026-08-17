"""PyMuPDF 기반 조항(clause) 헤딩 감지 및 계층 구조 파싱 (기획서 6절).

단독 실행:
    python -m core.pdf_parser <pdf경로> [--json]
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from core.config import BOLD_FONT_KEYWORD, HEADER_Y_THRESHOLD, X_TOLERANCE

# 조항번호 패턴: 순수 숫자 계층 ("8", "8.4", "8.4.2" ...)
NUMERIC_HEADING_RE = re.compile(r"^\d+(\.\d+){0,4}$")
# 부속서 타이틀: "부속서 A", "부속서A"
ANNEX_TITLE_RE = re.compile(r"^부속서\s?[A-Z]$")
# 부속서 하위 조항: "A.1", "A.1.2" ...
ANNEX_SUB_RE = re.compile(r"^[A-Z](\.\d+){1,4}$")


def _is_bold(font_name: str) -> bool:
    return BOLD_FONT_KEYWORD in (font_name or "")


def _match_heading_number(first_text: str) -> Optional[str]:
    text = first_text.strip()
    if NUMERIC_HEADING_RE.match(text):
        return text
    if ANNEX_TITLE_RE.match(text):
        return text
    if ANNEX_SUB_RE.match(text):
        return text
    return None


def _heading_level(clause_number: str) -> int:
    if ANNEX_TITLE_RE.match(clause_number):
        return 1
    return clause_number.count(".") + 1


def _collect_lines(page):
    """페이지의 텍스트 블록에서 line dict 목록을 순서대로 반환."""
    raw = page.get_text("dict")
    lines = []
    for block in raw.get("blocks", []):
        if block.get("type") != 0:  # 이미지 등 텍스트 아닌 블록 제외
            continue
        for line in block.get("lines", []):
            if line.get("spans"):
                lines.append(line)
    return lines


def _line_text(line) -> str:
    return "".join(span["text"] for span in line["spans"])


def _compute_left_baseline(all_page_lines) -> float:
    """문서 전체에서 가장 빈번한 라인 시작 x좌표(본문 좌측 정렬 기준값) 계산."""
    counter: Counter = Counter()
    for lines in all_page_lines:
        for line in lines:
            if line["bbox"][1] < HEADER_Y_THRESHOLD:
                continue
            counter[round(line["bbox"][0], 1)] += 1
    if not counter:
        return 0.0
    return counter.most_common(1)[0][0]


def parse_pdf(pdf_path: str) -> list:
    """PDF를 파싱하여 조항(clause) 딕셔너리 목록을 반환한다.

    각 clause는 parent_ref(부모 clause 딕셔너리 참조, 최상위는 None)와
    children(자식 목록, build_tree 호출 후 채워짐)을 포함한다.
    """
    doc = fitz.open(pdf_path)
    all_page_lines = [_collect_lines(doc[i]) for i in range(doc.page_count)]
    baseline_x = _compute_left_baseline(all_page_lines)

    clauses = []
    stack = []  # index i => level(i+1)의 최근 clause
    sort_counters = defaultdict(int)  # parent 식별자별 sort_order 카운터

    for page_index, lines in enumerate(all_page_lines):
        for li, line in enumerate(lines):
            bbox = line["bbox"]
            if bbox[1] < HEADER_Y_THRESHOLD:
                continue  # 페이지 상단 반복 헤더 노이즈 제외

            if line.get("_consumed"):
                continue

            spans = line["spans"]
            first_span = spans[0]
            first_text = first_span["text"].strip()

            clause_number = None
            if (
                first_text
                and _is_bold(first_span.get("font", ""))
                and abs(bbox[0] - baseline_x) <= X_TOLERANCE
            ):
                clause_number = _match_heading_number(first_text)

            if clause_number:
                title = "".join(s["text"] for s in spans[1:]).strip(" .\t")
                if not title and li + 1 < len(lines):
                    next_line = lines[li + 1]
                    next_first = next_line["spans"][0]
                    if (
                        next_line["bbox"][1] >= HEADER_Y_THRESHOLD
                        and not _is_bold(next_first.get("font", ""))
                    ):
                        title = _line_text(next_line).strip()
                        next_line["_consumed"] = True

                level = _heading_level(clause_number)
                del stack[level - 1:]
                parent = stack[-1] if stack else None
                parent_key = id(parent) if parent is not None else None
                sort_counters[parent_key] += 1

                clause = {
                    "clause_number": clause_number,
                    "title": title,
                    "body_text": "",
                    "page_number": page_index,
                    "level": level,
                    "sort_order": sort_counters[parent_key],
                    "parent_ref": parent,
                    "children": [],
                }
                stack.append(clause)
                clauses.append(clause)
            else:
                text = _line_text(line).strip()
                if not text or not stack:
                    continue
                leaf = stack[-1]
                leaf["body_text"] = (
                    f"{leaf['body_text']}\n{text}" if leaf["body_text"] else text
                )

    doc.close()
    return clauses


def build_tree(clauses: list) -> list:
    for c in clauses:
        c["children"] = []
    for c in clauses:
        parent = c["parent_ref"]
        if parent is not None:
            parent["children"].append(c)
    return [c for c in clauses if c["parent_ref"] is None]


def print_tree(roots: list, indent: int = 0) -> None:
    for node in roots:
        prefix = "  " * indent
        title = f" {node['title']}" if node["title"] else ""
        print(f"{prefix}{node['clause_number']}{title}  (p.{node['page_number'] + 1})")
        print_tree(node["children"], indent + 1)


def qa_report(clauses: list) -> None:
    total = len(clauses)
    level_counts = Counter(c["level"] for c in clauses)
    empty_body = [c for c in clauses if not c["body_text"]]
    orphan = [c for c in clauses if c["level"] > 1 and c["parent_ref"] is None]

    print("\n=== QA 리포트 ===")
    print(f"총 조항 수: {total}")
    print("레벨별 분포:")
    for level in sorted(level_counts):
        print(f"  level {level}: {level_counts[level]}개")
    print(f"본문(body_text) 비어있는 조항: {len(empty_body)}개")
    for c in empty_body[:20]:
        print(f"  - {c['clause_number']} {c['title']} (p.{c['page_number'] + 1})")
    if len(empty_body) > 20:
        print(f"  ... 외 {len(empty_body) - 20}개")
    print(f"부모 연결 끊긴(고아) 조항: {len(orphan)}개")
    for c in orphan[:20]:
        print(f"  - {c['clause_number']} {c['title']} (p.{c['page_number'] + 1})")


def _strip_refs(node: dict) -> dict:
    return {
        "clause_number": node["clause_number"],
        "title": node["title"],
        "body_text": node["body_text"],
        "page_number": node["page_number"],
        "level": node["level"],
        "sort_order": node["sort_order"],
        "children": [_strip_refs(ch) for ch in node["children"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF 규격 문서 조항 구조 파싱 (MVP 1단계)")
    parser.add_argument("pdf_path", help="파싱할 PDF 파일 경로")
    parser.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"파일을 찾을 수 없습니다: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    clauses = parse_pdf(args.pdf_path)
    roots = build_tree(clauses)

    if args.json:
        print(json.dumps([_strip_refs(r) for r in roots], ensure_ascii=False, indent=2))
    else:
        print_tree(roots)
        qa_report(clauses)


if __name__ == "__main__":
    main()
