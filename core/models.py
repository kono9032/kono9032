"""데이터 클래스 정의 (DB 테이블과 1:1 대응, 기획서 5절)."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Document:
    id: Optional[int]
    title: str
    file_path: str
    page_count: int
    added_at: Optional[str] = None


@dataclass
class Clause:
    id: Optional[int]
    document_id: Optional[int]
    parent_id: Optional[int]
    clause_number: Optional[str]
    title: Optional[str]
    body_text: Optional[str]
    page_number: int
    sort_order: int
    level: int
