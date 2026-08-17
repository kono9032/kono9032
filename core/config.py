"""전역 설정 상수."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "app.db"

# 파싱 관련 상수 (기획서 6.1절)
HEADER_Y_THRESHOLD = 55.0   # 페이지 상단 반복 헤더(문서명) 제외 기준 y좌표(pt)
X_TOLERANCE = 2.0           # 헤딩 x좌표와 본문 좌측 정렬 기준값 간 허용 오차(pt)
BOLD_FONT_KEYWORD = "Bold"  # 헤딩 폰트 판별 키워드
