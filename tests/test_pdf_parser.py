"""core.pdf_parser 단위/통합 테스트.

실제 KS 규격 PDF는 저작권상 저장소에 포함하지 않으므로, PyMuPDF로 동일한
레이아웃 규칙(볼드 헤딩 + 좌측 정렬 x좌표 + 조항번호 패턴)을 만족하는
합성 PDF를 테스트 시점에 생성하여 검증한다.
"""
import fitz
import pytest

from core.pdf_parser import (
    ANNEX_SUB_RE,
    ANNEX_TITLE_RE,
    NUMERIC_HEADING_RE,
    build_tree,
    parse_pdf,
)

BASE_X = 72.0


def _make_sample_pdf(path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # 페이지 상단 반복 헤더 노이즈 (y < 55) — 파싱에서 제외되어야 함
    page.insert_text((BASE_X, 30), "KS C IEC 60601-1:2020", fontsize=8, fontname="helv")

    y = 100

    def heading(number, title, dy=20):
        nonlocal y
        tw = fitz.get_text_length(number + " ", fontsize=10, fontname="hebo")
        page.insert_text((BASE_X, y), number + " ", fontsize=10, fontname="hebo")
        page.insert_text((BASE_X + tw, y), title, fontsize=10, fontname="helv")
        y += dy

    def plain(text, dy=20, bold=False):
        nonlocal y
        page.insert_text((BASE_X, y), text, fontsize=10, fontname="hebo" if bold else "helv")
        y += dy

    heading("8", "General requirements")
    plain("This is body text of clause 8, first sentence.")
    heading("8.4", "Rated voltage")
    plain("Body text of 8.4.")
    heading("8.4.1", "First sub clause")
    plain("Body of 8.4.1.")
    heading("8.4.2", "Rated voltage detail")
    plain("Body text of 8.4.2 first line.")
    plain("Note also see 5.9.2.1 reference")  # 오탐 방지: 첫 span이 볼드 아님
    plain("As defined in KS C IEC 60664-1:2007 clause 3.2, changed")
    plain("Table 8.4.2-1 is as follows")
    plain("8.5", bold=True)  # 번호만 있고 제목은 다음 줄
    plain("Maximum allowable current")
    plain("Body text of 8.5.")

    doc.save(str(path))
    doc.close()


@pytest.fixture()
def sample_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    _make_sample_pdf(pdf_path)
    return pdf_path


def test_extracts_expected_clause_numbers(sample_pdf):
    clauses = parse_pdf(str(sample_pdf))
    numbers = [c["clause_number"] for c in clauses]
    assert numbers == ["8", "8.4", "8.4.1", "8.4.2", "8.5"]


def test_false_positive_bold_references_not_treated_as_headings(sample_pdf):
    """문장 중간의 볼드 아닌 조항번호 인용(비고, 정의 등)이 헤딩으로 오인되지 않아야 함."""
    clauses = parse_pdf(str(sample_pdf))
    numbers = {c["clause_number"] for c in clauses}
    assert "5.9.2.1" not in numbers
    assert "3.2" not in numbers
    assert "8.4.2-1" not in numbers

    clause_842 = next(c for c in clauses if c["clause_number"] == "8.4.2")
    assert "5.9.2.1 reference" in clause_842["body_text"]
    assert "3.2, changed" in clause_842["body_text"]
    assert "Table 8.4.2-1" in clause_842["body_text"]


def test_title_on_next_line_is_captured(sample_pdf):
    clauses = parse_pdf(str(sample_pdf))
    clause_85 = next(c for c in clauses if c["clause_number"] == "8.5")
    assert clause_85["title"] == "Maximum allowable current"
    assert clause_85["body_text"] == "Body text of 8.5."


def test_hierarchy_levels_and_parenting(sample_pdf):
    clauses = parse_pdf(str(sample_pdf))
    roots = build_tree(clauses)

    assert len(roots) == 1
    root = roots[0]
    assert root["clause_number"] == "8"
    assert root["level"] == 1

    child_numbers = [c["clause_number"] for c in root["children"]]
    assert child_numbers == ["8.4", "8.5"]

    clause_84 = root["children"][0]
    grandchild_numbers = [c["clause_number"] for c in clause_84["children"]]
    assert grandchild_numbers == ["8.4.1", "8.4.2"]
    assert clause_84["children"][0]["level"] == 3


def test_header_noise_excluded_from_body(sample_pdf):
    clauses = parse_pdf(str(sample_pdf))
    for c in clauses:
        assert "KS C IEC 60601-1:2020" not in (c["body_text"] or "")


def test_no_orphans_or_empty_bodies(sample_pdf):
    clauses = parse_pdf(str(sample_pdf))
    orphans = [c for c in clauses if c["level"] > 1 and c["parent_ref"] is None]
    empty_bodies = [c for c in clauses if not c["body_text"]]
    assert orphans == []
    assert empty_bodies == []


# --- 정규식 단위 테스트 (부속서 패턴은 한글 폰트 렌더링 없이 직접 검증) ---

@pytest.mark.parametrize("text", ["8", "8.4", "8.4.2", "8.4.2.1"])
def test_numeric_heading_regex_matches(text):
    assert NUMERIC_HEADING_RE.match(text)


@pytest.mark.parametrize("text", ["8.", "8.4.2-1", "표8", "A.1"])
def test_numeric_heading_regex_rejects(text):
    assert not NUMERIC_HEADING_RE.match(text)


@pytest.mark.parametrize("text", ["부속서 A", "부속서A", "부속서 Z"])
def test_annex_title_regex_matches(text):
    assert ANNEX_TITLE_RE.match(text)


@pytest.mark.parametrize("text", ["A.1", "A.1.2"])
def test_annex_sub_regex_matches(text):
    assert ANNEX_SUB_RE.match(text)
