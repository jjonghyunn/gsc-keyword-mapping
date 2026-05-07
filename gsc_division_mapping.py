# gsc_division_mapping.py
# 2026-05-07  Jonghyun Park w/ Claude
#
# Google Search Console raw 데이터의 쿼리 텍스트 열에서 키워드를 substring 매칭해
# division(MX/VD/DA/...)으로 분류하는 스크립트.
#
# 동작:
#   - keyword → division 매핑은 gsc_division_keyword.csv 의 A열(Keyword), B열(Division)
#   - 대상 셀 텍스트 안에 키워드가 substring으로 들어 있으면 매칭(대소문자 무시)
#   - 한 셀에서 여러 division이 매칭되면 DIVISION_ORDER 순서로 정렬해 ", "로 join
#   - 매칭이 하나도 없으면 UNMATCHED_LABEL ('ETC')로 분류
#   - CSV에 키워드/Division이 추가되면 코드 수정 없이 자동 반영
#     (새 division은 DIVISION_ORDER 뒤에 알파벳 순으로 붙음 — 우선순위 고정 필요 시 추가)
#
# 사용:
#   1. KEYWORD_CSV / RAW_INPUT 경로 확인 (스크립트와 같은 폴더 권장)
#   2. MAPPINGS: (입력 열, 출력 열, 신규 컬럼명) 페어를 필요한 만큼 추가
#   3. DATE_FORMATTING: 날짜 컬럼 포맷 정규화 페어
#   4. 실행 → {입력파일명}_with_division.csv 저장

from pathlib import Path
import pandas as pd

# ── 경로 설정 ──────────────────────────────────────────────────────
# 키워드 매핑 CSV / raw 입력 모두 이 스크립트와 같은 폴더에 둘 것.
SCRIPT_DIR  = Path(__file__).parent
KEYWORD_CSV = SCRIPT_DIR / "gsc_division_keyword.csv"
RAW_INPUT   = SCRIPT_DIR / "gsc_mapping_test_raw.csv"   # csv 또는 xlsx
SHEET_NAME  = 0                                          # xlsx인 경우 sheet 인덱스/이름

# 매핑 페어 목록: (TARGET_COL, OUT_COL, NEW_OUT_COL_NAME)
# - TARGET_COL / OUT_COL은 엑셀 letter ('I', 'J') 또는 컬럼명 둘 다 OK
# - OUT_COL이 이미 있으면 덮어쓰기, 없으면 NEW_OUT_COL_NAME으로 신규 생성
# - 페어를 추가/제거해서 임의 개수의 매핑 동시 처리 가능
MAPPINGS = [
    ("I", "J", "division"),             # I열(Query Trans, EN) → J열
    ("B", "K", "division_local_lang"),  # B열(Query, 로컬어)   → K열
]

# Division 우선 순위 (출력 시 이 순서로 join)
DIVISION_ORDER = ["MX", "VD", "DA"]

# 매칭 실패 시 채울 값
UNMATCHED_LABEL = "ETC"

# 날짜 포맷 정규화: (TARGET_COL, strftime 포맷)
# - 엑셀 시리얼 숫자(45658) / 'yyyy-mm-dd' / 'yyyy-mm' 등 어떤 입력이든 지정 포맷으로 변환
DATE_FORMATTING = [
    ("A", "%Y-%m-%d"),   # A열 (Date)  → yyyy-mm-dd
    ("H", "%Y-%m"),      # H열 (Month) → yyyy-mm
]


# ── 엑셀 컬럼 letter → 0-based index ─────────────────────────────
def col_letter_to_idx(letter: str) -> int:
    letter = letter.strip().upper()
    idx = 0
    for c in letter:
        idx = idx * 26 + (ord(c) - ord("A") + 1)
    return idx - 1


def resolve_target_column(df: pd.DataFrame, spec: str) -> str:
    """spec이 엑셀 letter(A~ZZ)면 인덱스로, 그 외에는 컬럼명으로 해석.
       letter가 df 폭을 넘어가면 IndexError → 호출부에서 처리.
    """
    s = spec.strip()
    if s.isalpha() and len(s) <= 3:
        return df.columns[col_letter_to_idx(s)]
    return s


def resolve_out_column(df: pd.DataFrame, spec: str, new_name: str) -> str:
    """OUT_COL용. letter면 그 인덱스의 기존 컬럼 사용, 없으면 new_name으로 신규 생성.
       컬럼명을 직접 지정한 경우 → 그 이름 그대로(있든 없든) 반환.
    """
    s = spec.strip()
    if s.isalpha() and len(s) <= 3:
        idx = col_letter_to_idx(s)
        if idx < len(df.columns):
            return df.columns[idx]
        df[new_name] = ""
        return new_name
    return s


# ── 키워드 매핑 로드 ───────────────────────────────────────────────
def load_keyword_map(path: Path) -> list[tuple[str, str]]:
    """gsc_division_keyword.csv → [(keyword_lower, division), ...]
       길이 내림차순 정렬 — 디버그/로그상 긴 키워드가 짧은 키워드보다 먼저 보이게.
       (실제 매칭은 set으로 모으므로 순서가 결과에 영향 X)
    """
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    df = df[["Keyword", "Division"]].dropna()
    df["Keyword"]  = df["Keyword"].astype(str).str.strip().str.lower()
    df["Division"] = df["Division"].astype(str).str.strip().str.upper()
    df = df[(df["Keyword"] != "") & (df["Division"] != "")]
    df = df.drop_duplicates()
    pairs = list(df.itertuples(index=False, name=None))
    pairs.sort(key=lambda x: -len(x[0]))
    return pairs


# ── 단일 셀 → division 문자열 ─────────────────────────────────────
def map_divisions(text, kw_pairs: list[tuple[str, str]]) -> str:
    if pd.isna(text):
        return UNMATCHED_LABEL
    t = str(text).lower()
    if not t.strip():
        return UNMATCHED_LABEL
    found = set()
    for kw, div in kw_pairs:
        if kw in t:
            found.add(div)
    if not found:
        return UNMATCHED_LABEL
    ordered = [d for d in DIVISION_ORDER if d in found]
    extras  = sorted(d for d in found if d not in DIVISION_ORDER)
    return ", ".join(ordered + extras)


# ── 입력 로드 ──────────────────────────────────────────────────────
def read_raw(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, sheet_name=SHEET_NAME)
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


# ── 날짜 정규화 ────────────────────────────────────────────────────
# 엑셀 시리얼(숫자) → datetime 변환의 기준일 (1900 leap year bug 보정)
_EXCEL_EPOCH = pd.Timestamp("1899-12-30")


def normalize_date_column(s: pd.Series, fmt: str) -> pd.Series:
    """다음 케이스를 모두 받아서 strftime(fmt)로 통일:
       1) 엑셀 시리얼 숫자(45658) 또는 그것의 문자열형
       2) 'YYYY-MM-DD', 'YYYY/MM/DD' 등 일반 날짜 문자열
       3) 'YYYY-MM' (월 단위) — 1일로 처리
       파싱 실패 셀은 원본 값을 문자열 그대로 유지.
    """
    s = s.copy()
    raw = s.astype("object")

    # (1) 숫자/숫자 문자열 → 엑셀 시리얼로 우선 시도
    as_num = pd.to_numeric(s, errors="coerce")
    serial_dt = _EXCEL_EPOCH + pd.to_timedelta(as_num, unit="D")
    # 시리얼 범위 체크 — 1990~2099 정도 벗어나면 시리얼이 아님(우연한 숫자)
    valid_serial = (serial_dt >= "1990-01-01") & (serial_dt <= "2099-12-31")
    serial_dt = serial_dt.where(valid_serial)

    # (2) 시리얼이 아닌 셀은 일반 datetime 파싱
    str_dt = pd.to_datetime(s.where(serial_dt.isna()), errors="coerce")

    final_dt = serial_dt.fillna(str_dt)

    formatted = final_dt.dt.strftime(fmt)
    # 파싱 실패 셀은 원본 유지
    return formatted.fillna(raw.astype(str))


# ── 메인 ───────────────────────────────────────────────────────────
def main():
    print(f"▶ 키워드 매핑 로드: {KEYWORD_CSV}")
    kw_pairs = load_keyword_map(KEYWORD_CSV)
    by_div = {}
    for _, d in kw_pairs:
        by_div[d] = by_div.get(d, 0) + 1
    print(f"  키워드 총 {len(kw_pairs)}개  (MX={by_div.get('MX',0)} / VD={by_div.get('VD',0)} / DA={by_div.get('DA',0)})")

    print(f"\n▶ raw 입력 로드: {RAW_INPUT}")
    if not RAW_INPUT.exists():
        raise FileNotFoundError(f"입력 파일 없음: {RAW_INPUT}")
    df = read_raw(RAW_INPUT)
    print(f"  행수: {len(df):,}  /  컬럼: {list(df.columns)}")

    # 날짜 컬럼 포맷 정규화
    for date_spec, fmt in DATE_FORMATTING:
        col = resolve_target_column(df, date_spec)
        before = df[col].iloc[0] if len(df) else None
        df[col] = normalize_date_column(df[col], fmt)
        after = df[col].iloc[0] if len(df) else None
        print(f"  날짜 정규화: '{col}'  ({date_spec})  → {fmt}   샘플: {before!r} → {after!r}")

    for target_spec, out_spec, new_name in MAPPINGS:
        target  = resolve_target_column(df, target_spec)
        out_col = resolve_out_column(df, out_spec, new_name)
        print(f"\n▶ 매핑: '{target}'  (지정: {target_spec})  →  '{out_col}'  (지정: {out_spec})")

        df[out_col] = df[target].apply(lambda v: map_divisions(v, kw_pairs))

        matched = (df[out_col] != UNMATCHED_LABEL).sum()
        pct = (matched / len(df) * 100) if len(df) else 0.0
        print(f"  매칭된 행: {matched:,} / {len(df):,}  ({pct:.1f}%)  /  {UNMATCHED_LABEL}: {len(df)-matched:,}")
        print(f"  '{out_col}' 분포 (top 10):")
        print(df[out_col].value_counts().head(10).to_string())

    out_path = SCRIPT_DIR / f"{RAW_INPUT.stem}_with_division.csv"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[OK] 저장: {out_path}  ({len(df):,}행)")


if __name__ == "__main__":
    main()
