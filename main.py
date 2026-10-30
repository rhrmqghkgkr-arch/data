import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
APP_TITLE = "뇌졸중 예측 실습실"
DATA_URL = "https://raw.githubusercontent.com/rhrmqghkgkr-arch/data/main/stroke.csv"
RECORD_DIR = Path("내_기록")
RECORD_FILE = RECORD_DIR / "stroke_intro.json"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧠",
    layout="wide",
)

# 열 이름, 교재를 보고 직접 채울 우리말 뜻 입력란
COLUMNS = [
    "id",
    "gender",
    "age",
    "hypertension",
    "heart_disease",
    "ever_married",
    "work_type",
    "Residence_type",
    "avg_glucose_level",
    "bmi",
    "smoking_status",
    "stroke",
]


def load_saved_record():
    """저장된 우리말 뜻과 데이터 출처를 불러온다."""
    if RECORD_FILE.exists():
        try:
            with RECORD_FILE.open("r", encoding="utf-8") as file:
                saved = json.load(file)
            if not isinstance(saved, dict):
                return {"meanings": {}, "source": ""}
            return {
                "meanings": saved.get("meanings", {}),
                "source": saved.get("source", ""),
            }
        except (json.JSONDecodeError, OSError):
            st.warning("저장된 기록 파일을 읽지 못해 빈 입력란으로 시작합니다.")
    return {"meanings": {}, "source": ""}


def save_record(meanings, source):
    """입력 내용을 JSON UTF-8 파일로 저장한다."""
    RECORD_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "meanings": meanings,
        "source": source,
    }
    with RECORD_FILE.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


@st.cache_data
def load_data():
    """CSV를 UTF-8로 읽는다. bmi의 빈 값은 결측치로 유지한다."""
    data = pd.read_csv(DATA_URL, encoding="utf-8")
    # 안내된 데이터 열 순서를 유지하고, 예상하지 못한 열도 유실하지 않는다.
    existing = [column for column in COLUMNS if column in data.columns]
    remaining = [column for column in data.columns if column not in existing]
    return data[existing + remaining]


# ------------------------------------------------------------
# 화면 제목
# ------------------------------------------------------------
st.title("🧠 뇌졸중 예측 실습실")
st.caption("뇌졸중 데이터의 구조를 살펴보고, 변수의 의미를 직접 정리해 보는 실습 공간입니다.")
st.divider()

# ------------------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------------------
try:
    df = load_data()
except Exception as error:
    st.error("데이터를 불러오지 못했습니다. 인터넷 연결과 CSV 주소를 확인해 주세요.")
    st.exception(error)
    st.stop()

if "stroke" not in df.columns:
    st.error("데이터에 'stroke' 열이 없습니다. CSV 파일의 열 이름을 확인해 주세요.")
    st.stop()

total_people = len(df)
column_count = len(df.columns)
stroke_count = int((pd.to_numeric(df["stroke"], errors="coerce") == 1).sum())
stroke_ratio = (stroke_count / total_people * 100) if total_people else 0.0

# ------------------------------------------------------------
# 요약 숫자 카드 네 개
# ------------------------------------------------------------
st.subheader("데이터 한눈에 보기")
metric_cols = st.columns(4)
metrics = [
    ("전체 사람 수", f"{total_people:,}명"),
    ("열 개수", f"{column_count:,}개"),
    ("stroke가 1인 사람 수", f"{stroke_count:,}명"),
    ("stroke가 1인 비율", f"{stroke_ratio:.2f}%"),
]
for col, (label, value) in zip(metric_cols, metrics):
    with col:
        st.metric(label=label, value=value)

st.divider()

# ------------------------------------------------------------
# 열 정보 표 + 뜻 입력
# ------------------------------------------------------------
st.subheader("열 이름과 데이터 살펴보기")
st.write("‘우리말 뜻’은 교재를 참고해 직접 입력하세요. 입력한 내용은 자동으로 저장됩니다.")

saved = load_saved_record()
saved_meanings = saved.get("meanings", {})
meaning_values = {}

# 열 이름별 값의 종류와 결측치 수 계산
info_rows = []
for column in df.columns:
    info_rows.append(
        {
            "열 이름": column,
            "값의 종류": int(df[column].nunique(dropna=True)),
            "빈 값 개수": int(df[column].isna().sum()),
        }
    )
info_df = pd.DataFrame(info_rows)

# 열 정보 입력 UI
with st.form("column_meanings_form"):
    meaning_cols = st.columns(2)
    for index, column in enumerate(df.columns):
        with meaning_cols[index % 2]:
            meaning_values[column] = st.text_input(
                f"{column}의 우리말 뜻",
                value=str(saved_meanings.get(column, "")),
                key=f"meaning_{column}",
                placeholder="교재를 보고 우리말 뜻을 입력하세요",
            )
    source_value = st.text_area(
        "데이터 출처",
        value=str(saved.get("source", "")),
        placeholder="교재에 안내된 데이터 출처를 입력하세요.",
        height=90,
    )
    submitted = st.form_submit_button("입력 내용 저장", type="primary", use_container_width=True)

if submitted:
    try:
        save_record(meaning_values, source_value)
        st.success(f"입력 내용을 {RECORD_FILE.as_posix()} 파일에 저장했습니다.")
    except OSError as error:
        st.error("기록을 저장하지 못했습니다. 폴더 쓰기 권한을 확인해 주세요.")
        st.exception(error)

# 저장 여부와 무관하게 현재 화면에 입력된 뜻을 반영해 표를 구성
display_rows = []
for row in info_rows:
    column = row["열 이름"]
    display_rows.append(
        {
            "열 이름": column,
            "우리말 뜻": meaning_values.get(
                column,
                str(saved_meanings.get(column, "")),
            ),
            "값의 종류": row["값의 종류"],
            "빈 값 개수": row["빈 값 개수"],
        }
    )

st.dataframe(
    pd.DataFrame(display_rows),
    use_container_width=True,
    hide_index=True,
)

st.caption("값의 종류는 결측치를 제외한 서로 다른 값의 개수입니다. 빈 값 개수는 결측치 개수입니다.")

st.divider()

# ------------------------------------------------------------
# 처음 다섯 줄
# ------------------------------------------------------------
st.subheader("데이터 처음 다섯 줄")
st.dataframe(df.head(5), use_container_width=True, hide_index=True)

st.divider()

# ------------------------------------------------------------
# 데이터 출처
# ------------------------------------------------------------
st.subheader("데이터 출처")
st.write("교재에 적힌 데이터 출처를 위 입력란에 작성한 뒤 ‘입력 내용 저장’을 눌러 주세요.")
st.code(DATA_URL, language="text")

# JSON 파일에 저장되는 항목과 위치 안내
st.caption(f"우리말 뜻과 데이터 출처는 `{RECORD_FILE.as_posix()}`에 UTF-8 JSON 형식으로 저장됩니다.")
