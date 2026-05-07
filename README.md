# gsc-keyword-mapping

Google Search Console raw 데이터의 쿼리 텍스트를 키워드 매핑으로 division(`MX/VD/DA/...`)별 분류하는 파이썬 스크립트.

## 구조

```
.
├── gsc_division_mapping.py     # 메인 스크립트
├── gsc_division_keyword.csv    # 키워드 → division 매핑 (예시 템플릿)
├── LICENSE
└── README.md
```

## 동작 요약

- `gsc_division_keyword.csv`의 (Keyword, Division) 페어를 로드
- raw CSV/XLSX의 지정 열에서 각 셀 텍스트 안에 키워드가 **substring**으로 들어있으면 해당 division을 매칭(대소문자 무시)
- 한 셀에서 여러 division이 매칭되면 `DIVISION_ORDER = ["MX","VD","DA"]` 순서로 정렬 후 `", "`로 join
- 매칭 없으면 `"ETC"`
- CSV에 키워드/Division을 추가하면 코드 수정 없이 자동 반영. 새로운 division 라벨이 들어와도 동작 (우선순위 고정 필요 시 `DIVISION_ORDER`에 추가)

## 사용법

1. `gsc_division_keyword.csv`를 실제 사용할 키워드 셋으로 채움
   - `Keyword` 열: 매칭할 부분 문자열
   - `Division` 열: `MX` / `VD` / `DA` 등 라벨
2. raw 입력 파일을 같은 폴더에 두고 `gsc_division_mapping.py` 상단 상수 조정:
   ```python
   RAW_INPUT = SCRIPT_DIR / "your_raw_file.csv"

   MAPPINGS = [
       ("I", "J", "division"),             # I열 → J열
       ("B", "K", "division_local_lang"),  # B열 → K열
   ]

   DATE_FORMATTING = [
       ("A", "%Y-%m-%d"),
       ("H", "%Y-%m"),
   ]
   ```
3. 실행:
   ```bash
   python gsc_division_mapping.py
   ```
4. 결과: `{입력파일명}_with_division_{YYYYMMDD_HHMM}.csv` 가 같은 폴더에 저장됨 (실행 시각 기준 타임스탬프)

## 주요 상수

| 상수 | 설명 |
|---|---|
| `KEYWORD_CSV` | 키워드 매핑 CSV 경로 (기본: 스크립트 같은 폴더의 `gsc_division_keyword.csv`) |
| `RAW_INPUT` | raw 입력 파일 경로 (csv/xlsx) |
| `MAPPINGS` | `(target_col, out_col, new_col_name)` 페어 리스트. 엑셀 letter 또는 컬럼명 둘 다 지원 |
| `DIVISION_ORDER` | 출력 시 division 정렬 순서 |
| `UNMATCHED_LABEL` | 매칭 실패 시 채울 값 (기본 `"ETC"`) |
| `DATE_FORMATTING` | `(col, strftime_fmt)` 페어. 엑셀 시리얼 숫자 / 일반 날짜 문자열 / `yyyy-mm` 모두 받아 지정 포맷으로 통일 |

## 키워드 CSV 포맷

```csv
Keyword,Division
phone,MX
tablet,MX
tv,VD
monitor,VD
fridge,DA
```

- 한 키워드당 한 행
- 키워드는 lowercase 권장(매칭은 어차피 대소문자 무시)
- 동일 키워드를 여러 division에 매핑해도 됨(둘 다 매칭됨)
- 빈 행/빈 셀은 자동 무시

## 라이선스

MIT
