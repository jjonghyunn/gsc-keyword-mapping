# GSC Division Mapping  
<sub>2026-05-07  Jonghyun Park w/ Claude</sub>  

GSC raw 데이터의 쿼리 텍스트를 키워드 매칭으로 division(MX/VD/DA/ETC)별 분류.

## 폴더 구성

```
gsc-keyword-mapping/
├── gsc_division_mapping.py   # 메인 스크립트
├── gsc_division_keyword.csv          # 실 키워드 매핑 (130개, MX 62 / VD 27 / DA 41)
├── gsc_mapping_raw.csv               # raw 입력 (로컬 전용, repo 미포함)
└── gsc_mapping_raw_with_division_YYYYMMDD_HHMM.csv  # 실행 결과 (로컬 전용, repo 미포함)
```

## 입력 raw 컬럼 구조

| 열 | 컬럼명 | 비고 |
|---|---|---|
| A | Date | 엑셀 시리얼(45658) → `yyyy-mm-dd`로 정규화 |
| B | Query | 로컬어 검색어 — K열 매핑 대상 |
| C | Clicks | |
| D | Impressions | |
| E | CTR | |
| F | Position | |
| G | Site | |
| H | Month | `yyyy-mm` 유지 |
| I | Query Trans | EN 번역어 — J열 매핑 대상 |
| J | division | 결과 (I열 기준) |
| K | division_local_lang | 결과 (B열 기준, 신규) |

## 스크립트 주요 상수

```python
RAW_INPUT = SCRIPT_DIR / "gsc_mapping_raw.csv"

MAPPINGS = [
    ("I", "J", "division"),             # I열(EN) → J열
    ("B", "K", "division_local_lang"),  # B열(로컬어) → K열
]

DATE_FORMATTING = [
    ("A", "%Y-%m-%d"),   # Date
    ("H", "%Y-%m"),      # Month
]

DIVISION_ORDER  = ["MX", "VD", "DA"]
UNMATCHED_LABEL = "ETC"
```

매핑 페어 / 날짜 페어 추가는 위 리스트에 한 줄 추가만 하면 자동 반영.

## 실행

```powershell
python gsc_division_mapping.py
```

출력 파일명: `{입력파일 stem}_with_division_{YYYYMMDD_HHMM}.csv`
실행 시각 타임스탬프가 끝에 붙어 같은 raw로 여러 번 돌려도 덮어쓰기 X.

## 동작 요약

- `gsc_division_keyword.csv` 의 (Keyword, Division) 페어를 모두 로드
- 각 셀 텍스트(lowercase 처리) 안에 키워드가 substring으로 들어 있으면 매칭
- 한 셀 다중 매칭 → `MX, VD, DA` 순서로 정렬해 `", "` join
- 매칭 0건 → `ETC`
- 새 division 라벨이 CSV에 들어와도 동작 (정렬 우선순위는 `DIVISION_ORDER` 뒤에 알파벳순)

## 마지막 테스트 결과 (2026-05-07, 550,000행 샘플)

| 매핑 | 매칭률 | 분포 (top) |
|---|---|---|
| I열(EN) → J열 (`division`) | 58.1% | MX 289,846 / VD 18,280 / DA 10,758 / MX,VD 316 / VD,DA 50 / MX,DA 26 / **ETC 230,724** |
| B열(로컬어) → K열 (`division_local_lang`) | 52.3% | MX 267,880 / VD 16,889 / DA 2,865 / MX,VD 157 / MX,DA 13 / **ETC 262,196** |

샘플 검증:
- "brand product_type" → MX (galaxy 키워드 매칭)
- "brand tablet" → MX (tablet 키워드)
- "montre connectée brand" (FR) → ETC (로컬어에 매칭 키워드 없음), 번역어 "brand smartwatch" → MX (watch)
- "brand country" → ETC (제품 키워드 없음)

## 키워드 추가/수정

`gsc_division_keyword.csv` 의 행만 추가/수정하면 코드 수정 없이 다음 실행부터 반영.
- Keyword: lowercase 권장 (매칭은 어차피 대소문자 무시)
- Division: `MX` / `VD` / `DA` 등 라벨

## 공개 repo 참고

- 키워드 CSV는 placeholder로 sanitize된 템플릿 버전
- 실 운용 시 `gsc_division_keyword.csv`에 실제 키워드를 채워서 사용
