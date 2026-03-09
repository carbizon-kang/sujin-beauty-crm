"""
수진뷰티 고객 관리 프로그램 (Supabase 버전)
- 데이터는 Supabase 클라우드 DB에 저장됩니다
- 어디서든 URL로 접속 가능합니다
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import calendar as cal_module

# ─────────────────────────────────────────────
# Supabase REST API 설정 (supabase 라이브러리 없이 직접 호출)
# ─────────────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def _get(table: str, params: dict = None) -> list:
    res = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=_headers(), params=params)
    return res.json() if res.ok else []

def _post(table: str, data: dict) -> dict:
    res = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=_headers(), json=data)
    return res.json()

def _patch(table: str, match: dict, data: dict):
    params = {k: f"eq.{v}" for k, v in match.items()}
    requests.patch(f"{SUPABASE_URL}/rest/v1/{table}", headers=_headers(), params=params, json=data)

def _delete(table: str, match: dict):
    params = {k: f"eq.{v}" for k, v in match.items()}
    requests.delete(f"{SUPABASE_URL}/rest/v1/{table}", headers=_headers(), params=params)

# ─────────────────────────────────────────────
# 기본 시술종류 (DB에 없을 때 대비)
# ─────────────────────────────────────────────
DEFAULT_TREATMENT_TYPES = [
    "커트", "펌", "염색", "탈색", "클리닉 트리트먼트",
    "두피 관리", "피부 관리 (기본)", "피부 관리 (스페셜)",
    "제모", "눈썹 정리", "기타",
]

# ─────────────────────────────────────────────
# 데이터 함수 - 시술종류
# ─────────────────────────────────────────────

def 시술종류_불러오기() -> list:
    try:
        rows = _get("treatment_types", {"select": "type_name", "order": "sort_order.asc"})
        return [r["type_name"] for r in rows] if rows else DEFAULT_TREATMENT_TYPES
    except:
        return DEFAULT_TREATMENT_TYPES


def 시술종류_추가(종류명: str):
    rows = _get("treatment_types", {"select": "sort_order", "order": "sort_order.desc", "limit": "1"})
    다음순서 = (rows[0]["sort_order"] + 1) if rows else 1
    _post("treatment_types", {"type_name": 종류명, "sort_order": 다음순서})


def 시술종류_삭제(종류명: str):
    _delete("treatment_types", {"type_name": 종류명})


# ─────────────────────────────────────────────
# 데이터 함수 - 고객
# ─────────────────────────────────────────────

def 고객_불러오기() -> pd.DataFrame:
    rows = _get("customers", {"order": "id.asc"})
    if not rows:
        return pd.DataFrame(columns=["고객ID", "고객명", "휴대폰번호", "성별", "나이대", "등록일시", "메모"])
    df = pd.DataFrame(rows)
    return df.rename(columns={
        "customer_id": "고객ID", "name": "고객명", "phone": "휴대폰번호",
        "gender": "성별", "age_group": "나이대", "registered_at": "등록일시", "memo": "메모",
    })[["고객ID", "고객명", "휴대폰번호", "성별", "나이대", "등록일시", "메모"]]


def 신규_고객ID() -> str:
    rows = _get("customers", {"select": "customer_id"})
    if not rows:
        return "C001"
    번호목록 = []
    for r in rows:
        try:
            번호목록.append(int(r["customer_id"][1:]))
        except:
            pass
    return f"C{(max(번호목록) + 1):03d}" if 번호목록 else "C001"


def 전화번호_포맷(번호: str) -> str:
    """숫자만 추출 후 한국 전화번호 형식(010-xxxx-xxxx)으로 변환"""
    digits = ''.join(filter(str.isdigit, 번호))
    if len(digits) == 11:  # 010-xxxx-xxxx
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10:  # 02-xxxx-xxxx 또는 0xx-xxx-xxxx
        if digits.startswith('02'):
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        else:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return 번호  # 형식이 맞지 않으면 입력값 그대로 반환


def 고객_추가(고객명, 휴대폰번호, 성별="", 나이대="", 메모=""):
    _post("customers", {
        "customer_id":   신규_고객ID(),
        "name":          고객명.strip(),
        "phone":         휴대폰번호.strip(),
        "gender":        성별,
        "age_group":     나이대,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "memo":          메모.strip(),
    })


# ─────────────────────────────────────────────
# 데이터 함수 - 시술이력
# ─────────────────────────────────────────────

def 시술이력_불러오기() -> pd.DataFrame:
    rows = _get("treatments", {"order": "visit_date.desc"})
    if not rows:
        return pd.DataFrame(columns=["이력ID", "고객ID", "고객명", "방문일자", "시술종류", "사용제품", "단가", "메모"])
    df = pd.DataFrame(rows)
    df = df.rename(columns={
        "treatment_id": "이력ID", "customer_id": "고객ID", "customer_name": "고객명",
        "visit_date": "방문일자", "treatment_type": "시술종류",
        "product_used": "사용제품", "price": "단가", "memo": "메모",
    })
    df["단가"] = pd.to_numeric(df["단가"], errors="coerce").fillna(0)
    return df[["이력ID", "고객ID", "고객명", "방문일자", "시술종류", "사용제품", "단가", "메모"]]


def 신규_이력ID() -> str:
    rows = _get("treatments", {"select": "treatment_id"})
    if not rows:
        return "T001"
    번호목록 = []
    for r in rows:
        try:
            번호목록.append(int(r["treatment_id"][1:]))
        except:
            pass
    return f"T{(max(번호목록) + 1):03d}" if 번호목록 else "T001"


def 시술이력_추가(고객ID, 고객명, 방문일자, 시술종류, 사용제품, 단가, 메모=""):
    _post("treatments", {
        "treatment_id":  신규_이력ID(),
        "customer_id":   고객ID,
        "customer_name": 고객명,
        "visit_date":    str(방문일자),
        "treatment_type": 시술종류,
        "product_used":  사용제품.strip(),
        "price":         int(단가),
        "memo":          메모.strip(),
    })


def 시술이력_수정(이력ID, 방문일자, 시술종류, 사용제품, 단가, 메모):
    _patch("treatments", {"treatment_id": 이력ID}, {
        "visit_date":    str(방문일자),
        "treatment_type": 시술종류,
        "product_used":  사용제품.strip(),
        "price":         int(단가),
        "memo":          메모.strip(),
    })


def 시술이력_삭제(이력ID):
    _delete("treatments", {"treatment_id": 이력ID})


# ─────────────────────────────────────────────
# 데이터 함수 - 앱 설정 (비밀번호)
# ─────────────────────────────────────────────

def 예약_불러오기() -> pd.DataFrame:
    rows = _get("reservations", {"order": "reservation_date.asc,reservation_time.asc"})
    if not rows:
        return pd.DataFrame(columns=["예약ID", "고객ID", "고객명", "예약일", "예약시간", "시술종류", "메모", "상태"])
    df = pd.DataFrame(rows)
    return df.rename(columns={
        "reservation_id": "예약ID", "customer_id": "고객ID", "customer_name": "고객명",
        "reservation_date": "예약일", "reservation_time": "예약시간",
        "service_type": "시술종류", "memo": "메모", "status": "상태",
    })[["예약ID", "고객ID", "고객명", "예약일", "예약시간", "시술종류", "메모", "상태"]]


def 신규_예약ID() -> str:
    rows = _get("reservations", {"select": "reservation_id"})
    if not rows:
        return "R001"
    번호목록 = []
    for r in rows:
        try:
            번호목록.append(int(r["reservation_id"][1:]))
        except:
            pass
    return f"R{(max(번호목록) + 1):03d}" if 번호목록 else "R001"


def 예약_추가(고객ID, 고객명, 예약일, 예약시간, 시술종류, 메모=""):
    _post("reservations", {
        "reservation_id":   신규_예약ID(),
        "customer_id":      고객ID,
        "customer_name":    고객명,
        "reservation_date": str(예약일),
        "reservation_time": str(예약시간),
        "service_type":     시술종류,
        "memo":             메모.strip(),
        "status":           "예약",
    })


def 예약_수정(예약ID, 예약일, 예약시간, 시술종류, 메모, 상태):
    _patch("reservations", {"reservation_id": 예약ID}, {
        "reservation_date": str(예약일),
        "reservation_time": str(예약시간),
        "service_type":     시술종류,
        "memo":             메모.strip(),
        "status":           상태,
    })


def 예약_삭제(예약ID):
    _delete("reservations", {"reservation_id": 예약ID})


def _get_app_password() -> str:
    """Supabase app_settings 테이블에서 비밀번호를 가져옵니다. 없으면 secrets 기본값 사용."""
    try:
        rows = _get("app_settings", {"select": "value", "key": "eq.app_password"})
        if rows and rows[0].get("value"):
            return rows[0]["value"]
    except:
        pass
    return st.secrets.get("APP_PASSWORD", "sujin1234")


def _set_app_password(new_pw: str) -> bool:
    """Supabase app_settings 테이블에 비밀번호를 저장합니다."""
    hdrs = {**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/app_settings",
        headers=hdrs,
        json={"key": "app_password", "value": new_pw},
    )
    return res.ok


# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="수진뷰티 고객 관리", page_icon="💄", layout="wide")

# ─────────────────────────────────────────────
# 로그인 체크
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("💄 수진뷰티 고객 관리 시스템")
    st.divider()
    col_center = st.columns([1, 1, 1])[1]
    with col_center:
        st.subheader("🔐 로그인")
        pw = st.text_input("비밀번호를 입력하세요", type="password", placeholder="비밀번호")
        if st.button("로그인", use_container_width=True, type="primary"):
            if pw == _get_app_password():
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

st.title("💄 수진뷰티 고객 관리 시스템")

# 로그아웃 / 비밀번호 변경 (우상단)
col_title, col_pw, col_logout = st.columns([7, 1.5, 1])
with col_pw:
    with st.popover("🔑 비밀번호 변경"):
        with st.form("비밀번호변경폼"):
            현재pw = st.text_input("현재 비밀번호", type="password")
            새pw   = st.text_input("새 비밀번호", type="password")
            확인pw = st.text_input("새 비밀번호 확인", type="password")
            변경버튼 = st.form_submit_button("변경", type="primary", use_container_width=True)
        if 변경버튼:
            if 현재pw != _get_app_password():
                st.error("현재 비밀번호가 틀렸습니다.")
            elif len(새pw) < 4:
                st.error("비밀번호는 4자 이상이어야 합니다.")
            elif 새pw != 확인pw:
                st.error("새 비밀번호가 일치하지 않습니다.")
            elif _set_app_password(새pw):
                st.success("비밀번호가 변경되었습니다!")
            else:
                st.error("변경 실패. Supabase app_settings 테이블을 확인하세요.")
with col_logout:
    if st.button("로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.divider()

탭1, 탭2, 탭3, 탭4, 탭5, 탭6, 탭7, 탭8, 탭9 = st.tabs([
    "👤 고객 등록",
    "✂️ 시술 이력 등록",
    "🔍 개인별 조회",
    "📊 매출 통계",
    "📋 고객 전체 리스트",
    "⚙️ 시술종류 관리",
    "📱 단체문자",
    "📥 데이터 가져오기",
    "📅 예약 관리",
])


# ════════════════════════════════════════════
# 탭1: 고객 등록
# ════════════════════════════════════════════
with 탭1:
    st.subheader("신규 고객 등록")

    with st.form("고객등록폼", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            고객명 = st.text_input("고객 이름 *", placeholder="예: 홍길동")
        with col2:
            휴대폰번호 = st.text_input("휴대폰 번호 *", placeholder="예: 010-1234-5678")
        col3, col4 = st.columns(2)
        with col3:
            성별 = st.radio("성별", ["여", "남", "미입력"], horizontal=True)
        with col4:
            나이대 = st.selectbox("나이대", ["미입력", "10대", "20대", "30대", "40대", "50대", "60대 이상"])
        메모 = st.text_area("메모 (특이사항, 선호 스타일 등)", height=80)
        저장 = st.form_submit_button("고객 등록", use_container_width=True, type="primary")

    if 저장:
        if not 고객명.strip():
            st.error("고객 이름을 입력해주세요.")
        elif not 휴대폰번호.strip():
            st.error("휴대폰 번호를 입력해주세요.")
        else:
            포맷번호 = 전화번호_포맷(휴대폰번호)
            digits = ''.join(filter(str.isdigit, 휴대폰번호))
            if len(digits) not in (10, 11):
                st.error("올바른 전화번호를 입력해주세요. 예: 010-1234-5678 또는 01012345678")
            else:
                고객_추가(고객명, 포맷번호, 성별, 나이대, 메모)
                st.success(f"'{고객명}' 고객이 등록되었습니다! (번호: {포맷번호})")
                st.balloons()

    st.divider()
    st.subheader("등록된 고객 현황")
    df_c = 고객_불러오기()
    if df_c.empty:
        st.info("아직 등록된 고객이 없습니다.")
    else:
        st.dataframe(df_c, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(df_c)}명 등록됨")


# ════════════════════════════════════════════
# 탭2: 시술 이력 등록
# ════════════════════════════════════════════
with 탭2:
    st.subheader("시술 이력 등록 (방문 기록 추가)")

    df_c = 고객_불러오기()
    시술목록 = 시술종류_불러오기()

    if df_c.empty:
        st.warning("먼저 '고객 등록' 탭에서 고객을 등록해주세요.")
    else:
        검색어2 = st.text_input("고객 이름 검색", placeholder="이름 입력 시 목록이 좁혀집니다", key="시술등록검색")
        필터df2 = df_c[df_c["고객명"].str.contains(검색어2.strip(), na=False)] if 검색어2.strip() else df_c

        if 필터df2.empty:
            st.warning(f"'{검색어2}' 이름의 고객이 없습니다.")
        else:
            고객_옵션 = {
                f"{row['고객명']} ({row['고객ID']})": (row["고객ID"], row["고객명"])
                for _, row in 필터df2.iterrows()
            }

            with st.form("시술등록폼", clear_on_submit=True):
                선택 = st.selectbox("고객 선택 *", list(고객_옵션.keys()))
                col1, col2 = st.columns(2)
                with col1:
                    방문일자 = st.date_input("방문일자 *", value=date.today())
                    시술종류 = st.selectbox("시술 종류 *", 시술목록)
                with col2:
                    사용제품 = st.text_input("사용 제품", placeholder="예: 엘라스틴 펌제 2제")
                    단가 = st.number_input("단가 (원) *", min_value=0, step=1000, value=0)
                메모 = st.text_area("메모", height=68)
                저장2 = st.form_submit_button("이력 저장", use_container_width=True, type="primary")

            if 저장2:
                고객ID, 고객명2 = 고객_옵션[선택]
                시술이력_추가(고객ID, 고객명2, 방문일자, 시술종류, 사용제품, 단가, 메모)
                st.success(f"'{고객명2}' 님의 시술 이력이 저장되었습니다!")

    st.divider()
    st.subheader("시술 이력 수정 / 삭제")

    df_t = 시술이력_불러오기()
    if df_t.empty:
        st.info("아직 등록된 시술 이력이 없습니다.")
    else:
        시술목록2 = 시술종류_불러오기()
        이력_옵션 = {
            f"{row['이력ID']} | {row['고객명']} | {row['방문일자']} | {row['시술종류']}": row["이력ID"]
            for _, row in df_t.iterrows()
        }

        선택이력라벨 = st.selectbox("수정/삭제할 이력 선택", list(이력_옵션.keys()), key="이력선택")
        선택이력ID  = 이력_옵션[선택이력라벨]
        원본 = df_t[df_t["이력ID"] == 선택이력ID].iloc[0]

        with st.form("이력수정폼"):
            st.caption(f"이력ID: {선택이력ID}  |  고객: {원본['고객명']}")
            col1, col2 = st.columns(2)
            with col1:
                수정_방문일자 = st.date_input(
                    "방문일자",
                    value=datetime.strptime(str(원본["방문일자"])[:10], "%Y-%m-%d").date(),
                )
                현재시술 = str(원본["시술종류"])
                수정_시술목록 = 시술목록2 if 현재시술 in 시술목록2 else [현재시술] + 시술목록2
                수정_시술종류 = st.selectbox("시술 종류", 수정_시술목록, index=수정_시술목록.index(현재시술))
            with col2:
                수정_사용제품 = st.text_input("사용 제품", value=str(원본["사용제품"]) if pd.notna(원본["사용제품"]) else "")
                수정_단가     = st.number_input("단가 (원)", min_value=0, step=1000, value=int(원본["단가"]))
            수정_메모 = st.text_area("메모", value=str(원본["메모"]) if pd.notna(원본["메모"]) else "", height=68)

            col_저장, col_삭제 = st.columns(2)
            수정저장 = col_저장.form_submit_button("수정 저장", use_container_width=True, type="primary")
            삭제확인 = col_삭제.form_submit_button("이 이력 삭제", use_container_width=True, type="secondary")

        if 수정저장:
            시술이력_수정(선택이력ID, 수정_방문일자, 수정_시술종류, 수정_사용제품, 수정_단가, 수정_메모)
            st.success(f"{선택이력ID} 이력이 수정되었습니다!")
            st.rerun()

        if 삭제확인:
            시술이력_삭제(선택이력ID)
            st.success(f"{선택이력ID} 이력이 삭제되었습니다.")
            st.rerun()

    st.divider()
    st.subheader("최근 시술 이력")
    df_t2 = 시술이력_불러오기()
    if df_t2.empty:
        st.info("아직 등록된 시술 이력이 없습니다.")
    else:
        st.dataframe(df_t2.head(20), use_container_width=True, hide_index=True)


# ════════════════════════════════════════════
# 탭3: 개인별 조회
# ════════════════════════════════════════════
with 탭3:
    st.subheader("개인별 방문 이력 및 매출 조회")

    df_c = 고객_불러오기()
    df_t = 시술이력_불러오기()

    if df_c.empty:
        st.warning("등록된 고객이 없습니다.")
    else:
        검색어3 = st.text_input("이름으로 검색", placeholder="이름 입력 시 목록이 좁혀집니다", key="개인조회검색")
        필터df = df_c[df_c["고객명"].str.contains(검색어3.strip(), na=False)] if 검색어3.strip() else df_c

        if 필터df.empty:
            st.warning(f"'{검색어3}' 이름의 고객이 없습니다.")
            st.stop()

        고객_옵션2 = {
            f"{row['고객명']} ({row['고객ID']})": row["고객ID"]
            for _, row in 필터df.iterrows()
        }
        선택2  = st.selectbox("고객을 선택하세요", list(고객_옵션2.keys()), key="개인조회")
        선택_ID = 고객_옵션2[선택2]

        고객정보  = df_c[df_c["고객ID"] == 선택_ID].iloc[0]
        성별표시  = str(고객정보.get("성별", "")) if pd.notna(고객정보.get("성별", "")) else ""
        나이대표시 = str(고객정보.get("나이대", "")) if pd.notna(고객정보.get("나이대", "")) else ""
        태그 = " · ".join(filter(lambda x: x and x != "미입력", [성별표시, 나이대표시]))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("고객명", 고객정보["고객명"])
        col2.metric("휴대폰", 고객정보["휴대폰번호"])
        col3.metric("성별/나이대", 태그 if 태그 else "-")
        col4.metric("등록일", str(고객정보["등록일시"])[:10] if pd.notna(고객정보["등록일시"]) else "-")

        if pd.notna(고객정보["메모"]) and 고객정보["메모"]:
            st.caption(f"메모: {고객정보['메모']}")

        st.divider()

        개인이력 = df_t[df_t["고객ID"] == 선택_ID].copy()

        if 개인이력.empty:
            st.info("아직 시술 이력이 없습니다.")
        else:
            개인이력 = 개인이력.sort_values("방문일자", ascending=False)
            총매출  = 개인이력["단가"].sum()
            총방문  = len(개인이력)
            마지막방문 = 개인이력["방문일자"].max()

            c1, c2, c3 = st.columns(3)
            c1.metric("총 방문 횟수", f"{총방문}회")
            c2.metric("누적 매출", f"{int(총매출):,}원")
            c3.metric("최근 방문일", 마지막방문)

            st.subheader("방문 이력 상세")
            표시컬럼 = ["방문일자", "시술종류", "사용제품", "단가", "메모"]
            st.dataframe(
                개인이력[표시컬럼].reset_index(drop=True),
                use_container_width=True, hide_index=True,
                column_config={"단가": st.column_config.NumberColumn("단가(원)", format="%d원")},
            )

            csv = 개인이력.to_csv(index=False).encode("utf-8-sig")
            st.download_button("이력 CSV 다운로드", data=csv,
                file_name=f"수진뷰티_{고객정보['고객명']}_이력.csv", mime="text/csv")


# ════════════════════════════════════════════
# 탭4: 매출 통계
# ════════════════════════════════════════════
with 탭4:
    st.subheader("매출 통계")
    df_t = 시술이력_불러오기()

    if df_t.empty:
        st.info("시술 이력 데이터가 없습니다.")
    else:
        df_t["방문일자"] = pd.to_datetime(df_t["방문일자"], errors="coerce")
        df_t["연도"] = df_t["방문일자"].dt.year.astype("Int64")
        df_t["월"]   = df_t["방문일자"].dt.month.astype("Int64")
        df_t["날짜"] = df_t["방문일자"].dt.date

        기간구분 = st.radio("조회 기간", ["일별", "월별", "연간"], horizontal=True)

        if 기간구분 == "일별":
            연도목록 = sorted(df_t["연도"].dropna().unique(), reverse=True)
            선택연도 = st.selectbox("연도 선택", 연도목록)
            월목록   = sorted(df_t[df_t["연도"] == 선택연도]["월"].dropna().unique())
            선택월   = st.selectbox("월 선택", 월목록, format_func=lambda x: f"{x}월")
            필터 = df_t[(df_t["연도"] == 선택연도) & (df_t["월"] == 선택월)]
            집계 = 필터.groupby("날짜")["단가"].sum().reset_index()
            집계.columns = ["날짜", "매출"]
            집계["날짜"] = 집계["날짜"].astype(str)
            st.metric(f"{선택연도}년 {선택월}월 총 매출", f"{int(집계['매출'].sum()):,}원")
            st.bar_chart(집계.set_index("날짜")["매출"])
            st.dataframe(집계.assign(매출=집계["매출"].apply(lambda x: f"{int(x):,}원")),
                         use_container_width=True, hide_index=True)

        elif 기간구분 == "월별":
            연도목록 = sorted(df_t["연도"].dropna().unique(), reverse=True)
            선택연도 = st.selectbox("연도 선택", 연도목록, key="월별연도")
            필터 = df_t[df_t["연도"] == 선택연도]
            집계 = 필터.groupby("월")["단가"].sum().reset_index()
            집계.columns = ["월", "매출"]
            집계["월표시"] = 집계["월"].apply(lambda x: f"{x}월")
            st.metric(f"{선택연도}년 연간 총 매출", f"{int(집계['매출'].sum()):,}원")
            st.bar_chart(집계.set_index("월표시")["매출"])
            st.dataframe(
                집계[["월표시", "매출"]].rename(columns={"월표시": "월"})
                .assign(매출=집계["매출"].apply(lambda x: f"{int(x):,}원")),
                use_container_width=True, hide_index=True)

        else:
            집계 = df_t.groupby("연도")["단가"].sum().reset_index()
            집계.columns = ["연도", "매출"]
            집계["연도"] = 집계["연도"].astype(str) + "년"
            st.metric("전체 누적 매출", f"{int(집계['매출'].sum()):,}원")
            st.bar_chart(집계.set_index("연도")["매출"])
            st.dataframe(집계.assign(매출=집계["매출"].apply(lambda x: f"{int(x):,}원")),
                         use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("시술 종류별 매출 비중")
        시술별 = df_t.groupby("시술종류")["단가"].sum().reset_index()
        시술별.columns = ["시술종류", "매출"]
        st.bar_chart(시술별.sort_values("매출", ascending=False).set_index("시술종류")["매출"])


# ════════════════════════════════════════════
# 탭5: 고객 전체 리스트
# ════════════════════════════════════════════
with 탭5:
    st.subheader("고객 전체 리스트")

    df_c = 고객_불러오기()
    df_t = 시술이력_불러오기()

    if df_c.empty:
        st.info("등록된 고객이 없습니다.")
    else:
        if not df_t.empty:
            요약 = df_t.groupby("고객ID").agg(
                방문횟수=("이력ID", "count"),
                마지막방문=("방문일자", "max"),
                누적매출=("단가", "sum"),
            ).reset_index()
            리스트 = df_c.merge(요약, on="고객ID", how="left")
            리스트["방문횟수"] = 리스트["방문횟수"].fillna(0).astype(int)
            리스트["누적매출"] = 리스트["누적매출"].fillna(0).astype(int)
            리스트["마지막방문"] = 리스트["마지막방문"].fillna("-")
        else:
            리스트 = df_c.copy()
            리스트["방문횟수"] = 0
            리스트["마지막방문"] = "-"
            리스트["누적매출"] = 0

        검색 = st.text_input("이름 또는 전화번호 검색", placeholder="검색어를 입력하세요")
        if 검색.strip():
            마스크 = (
                리스트["고객명"].str.contains(검색.strip(), na=False) |
                리스트["휴대폰번호"].str.contains(검색.strip(), na=False)
            )
            리스트 = 리스트[마스크]

        표시 = 리스트[["고객ID", "고객명", "휴대폰번호", "방문횟수", "마지막방문", "누적매출", "등록일시", "메모"]]
        st.dataframe(표시, use_container_width=True, hide_index=True,
            column_config={
                "누적매출": st.column_config.NumberColumn("누적매출(원)", format="%d원"),
                "방문횟수": st.column_config.NumberColumn("방문횟수", format="%d회"),
            })
        st.caption(f"총 {len(표시)}명")

        csv = 표시.to_csv(index=False).encode("utf-8-sig")
        st.download_button("전체 리스트 CSV 다운로드", data=csv,
            file_name=f"수진뷰티_전체고객_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv")


# ════════════════════════════════════════════
# 탭6: 시술종류 관리
# ════════════════════════════════════════════
with 탭6:
    st.subheader("시술 종류 관리")
    st.caption("추가/삭제한 시술 종류는 '시술 이력 등록' 탭에 즉시 반영됩니다.")

    시술목록 = 시술종류_불러오기()

    with st.form("시술추가폼", clear_on_submit=True):
        새시술 = st.text_input("새 시술 종류 입력", placeholder="예: 헤어 에센스 트리트먼트")
        추가버튼 = st.form_submit_button("추가", type="primary")

    if 추가버튼:
        새시술 = 새시술.strip()
        if not 새시술:
            st.error("시술 종류를 입력해주세요.")
        elif 새시술 in 시술목록:
            st.warning(f"'{새시술}'은 이미 목록에 있습니다.")
        else:
            시술종류_추가(새시술)
            st.success(f"'{새시술}'이 추가되었습니다!")
            st.rerun()

    st.divider()
    st.subheader("현재 시술 종류 목록")

    시술목록 = 시술종류_불러오기()
    if not 시술목록:
        st.info("등록된 시술 종류가 없습니다.")
    else:
        for i, 종류 in enumerate(시술목록):
            col_이름, col_버튼 = st.columns([6, 1])
            col_이름.write(f"**{i+1}.** {종류}")
            if col_버튼.button("삭제", key=f"del_{i}", type="secondary"):
                시술종류_삭제(종류)
                st.success(f"'{종류}'이 삭제되었습니다.")
                st.rerun()


# ════════════════════════════════════════════
# 탭7: 단체문자
# ════════════════════════════════════════════
with 탭7:
    st.subheader("단체문자 발송 준비")

    df_c = 고객_불러오기()
    df_t = 시술이력_불러오기()

    if df_c.empty:
        st.warning("등록된 고객이 없습니다.")
    else:
        st.subheader("1단계: 수신자 선택")

        방식 = st.radio("수신 대상", ["전체 고객", "미방문 고객 선별 (마지막 방문 기준)", "직접 선택"], horizontal=True)

        if 방식 == "전체 고객":
            수신자_df = df_c[["고객명", "휴대폰번호"]].copy()

        elif 방식 == "미방문 고객 선별 (마지막 방문 기준)":
            기준일수 = st.slider("마지막 방문으로부터 며칠 이상 지난 고객", 30, 365, 90, step=10, format="%d일")
            if not df_t.empty:
                df_t2 = df_t.copy()
                df_t2["방문일자"] = pd.to_datetime(df_t2["방문일자"], errors="coerce")
                마지막방문 = df_t2.groupby("고객ID")["방문일자"].max().reset_index()
                마지막방문.columns = ["고객ID", "마지막방문"]
                merged = df_c.merge(마지막방문, on="고객ID", how="left")
                기준날짜 = pd.Timestamp(date.today()) - pd.Timedelta(days=기준일수)
                조건 = merged["마지막방문"].isna() | (merged["마지막방문"] < 기준날짜)
                수신자_df = merged[조건][["고객명", "휴대폰번호"]].copy()
            else:
                수신자_df = df_c[["고객명", "휴대폰번호"]].copy()

        else:
            선택고객 = st.multiselect("문자 받을 고객을 선택하세요", options=df_c["고객명"].tolist())
            수신자_df = df_c[df_c["고객명"].isin(선택고객)][["고객명", "휴대폰번호"]].copy()

        수신자_df = 수신자_df.reset_index(drop=True)
        st.info(f"선택된 수신자: **{len(수신자_df)}명**")
        if not 수신자_df.empty:
            st.dataframe(수신자_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("2단계: 문자 내용 작성")

        템플릿 = st.selectbox("빠른 템플릿 선택", [
            "직접 입력",
            "안녕하세요! 수진뷰티입니다. 오랜만에 방문해 주세요 :) 이번 달 특별 할인 이벤트 중입니다!",
            "안녕하세요! 수진뷰티입니다. 방문하신 지 시간이 지났는데, 이번 주에 한번 오세요~",
            "수진뷰티 신규 시술 안내드립니다. 궁금하신 점은 언제든지 연락 주세요!",
        ])

        기본문구 = "" if 템플릿 == "직접 입력" else 템플릿
        문자내용 = st.text_area("문자 내용 *", value=기본문구, height=150,
                              placeholder="보낼 문자 내용을 입력하세요.")

        글자수 = len(문자내용)
        색상 = "🟢" if 글자수 <= 80 else ("🟡" if 글자수 <= 2000 else "🔴")
        st.caption(f"{색상} {글자수}자  |  80자 이하: SMS(단문) / 81~2000자: MMS(장문)")

        st.divider()
        st.subheader("3단계: 발송용 데이터 복사")

        if 수신자_df.empty:
            st.warning("수신자를 먼저 선택해주세요.")
        elif not 문자내용.strip():
            st.warning("문자 내용을 입력해주세요.")
        else:
            번호목록 = ", ".join(수신자_df["휴대폰번호"].tolist())
            col_a, col_b = st.columns(2)
            with col_a:
                st.text_area("수신자 번호 목록 (복사하세요)", value=번호목록, height=120)
            with col_b:
                st.text_area("발송 문자 내용 (복사하세요)", value=문자내용, height=120)

            st.info("위 번호 목록과 문자 내용을 복사해서 카카오톡 단체 메시지, 알리고 등의 서비스에 붙여넣기 하세요.")

            발송데이터 = 수신자_df.copy()
            발송데이터["문자내용"] = 문자내용
            csv발송 = 발송데이터.to_csv(index=False).encode("utf-8-sig")
            st.download_button("발송 목록 CSV 다운로드", data=csv발송,
                file_name=f"수진뷰티_문자발송_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv")


# ════════════════════════════════════════════
# 탭8: 데이터 가져오기 (엑셀 업로드)
# ════════════════════════════════════════════
with 탭8:
    st.subheader("📥 기존 데이터 가져오기 (엑셀 업로드)")
    st.info("기존 프로그램에서 사용하던 엑셀 파일을 업로드하면 자동으로 DB에 등록됩니다.")

    가져오기종류 = st.radio("가져올 데이터 선택", ["👤 고객 명단", "✂️ 시술 이력"], horizontal=True)

    # ── 양식 다운로드 ──
    with st.expander("📄 엑셀 양식 다운로드 (양식에 맞게 작성 후 업로드)"):
        if 가져오기종류 == "👤 고객 명단":
            샘플 = pd.DataFrame({
                "고객명": ["홍길동", "김수진"],
                "휴대폰번호": ["010-1234-5678", "010-9876-5432"],
                "성별": ["남", "여"],
                "나이대": ["30대", "40대"],
                "메모": ["드라이 선호", ""],
            })
        else:
            샘플 = pd.DataFrame({
                "고객명": ["홍길동", "김수진"],
                "방문일자": ["2025-01-15", "2025-02-20"],
                "시술종류": ["커트", "염색"],
                "사용제품": ["", "엘라스틴 7제"],
                "단가": [15000, 80000],
                "메모": ["", ""],
            })
        양식csv = 샘플.to_csv(index=False).encode("utf-8-sig")
        파일명 = "고객명단_양식.csv" if 가져오기종류 == "👤 고객 명단" else "시술이력_양식.csv"
        st.dataframe(샘플, use_container_width=True, hide_index=True)
        st.download_button("양식 CSV 다운로드", data=양식csv, file_name=파일명, mime="text/csv")

    st.divider()

    # ── 파일 업로드 ──
    업로드파일 = st.file_uploader(
        "엑셀(.xlsx) 또는 CSV(.csv) 파일 업로드",
        type=["xlsx", "xls", "csv"],
        help="첫 번째 시트의 데이터를 읽습니다."
    )

    if 업로드파일:
        try:
            if 업로드파일.name.endswith(".csv"):
                df_upload = pd.read_csv(업로드파일, dtype=str).fillna("")
            else:
                df_upload = pd.read_excel(업로드파일, dtype=str).fillna("")
            st.success(f"파일 로드 완료: {len(df_upload)}행")
        except Exception as e:
            st.error(f"파일 읽기 오류: {e}")
            df_upload = None

        if df_upload is not None and not df_upload.empty:
            st.subheader("미리보기 (상위 5행)")
            st.dataframe(df_upload.head(), use_container_width=True, hide_index=True)

            st.subheader("컬럼 매핑")
            컬럼목록 = ["(사용안함)"] + list(df_upload.columns)

            def 컬럼선택(라벨, 기본후보들):
                """업로드 파일 컬럼 중 기본 후보 이름과 일치하는 컬럼을 자동 선택"""
                for 후보 in 기본후보들:
                    if 후보 in df_upload.columns:
                        return st.selectbox(라벨, 컬럼목록, index=컬럼목록.index(후보))
                return st.selectbox(라벨, 컬럼목록)

            if 가져오기종류 == "👤 고객 명단":
                col1, col2 = st.columns(2)
                with col1:
                    col_name  = 컬럼선택("고객명 컬럼 *", ["고객명", "이름", "성함"])
                    col_phone = 컬럼선택("휴대폰번호 컬럼 *", ["휴대폰번호", "전화번호", "연락처", "휴대폰"])
                    col_gender = 컬럼선택("성별 컬럼", ["성별"])
                with col2:
                    col_age  = 컬럼선택("나이대 컬럼", ["나이대", "연령대"])
                    col_memo = 컬럼선택("메모 컬럼", ["메모", "특이사항"])

                if st.button("고객 명단 가져오기", type="primary", use_container_width=True):
                    if col_name == "(사용안함)" or col_phone == "(사용안함)":
                        st.error("고객명과 휴대폰번호 컬럼은 반드시 선택해야 합니다.")
                    else:
                        성공, 실패, 중복 = 0, 0, 0
                        기존고객 = 고객_불러오기()
                        기존번호목록 = 기존고객["휴대폰번호"].tolist() if not 기존고객.empty else []

                        진행바 = st.progress(0)
                        for i, row in df_upload.iterrows():
                            이름 = str(row.get(col_name, "")).strip()
                            번호 = str(row.get(col_phone, "")).strip()
                            if not 이름 or not 번호:
                                실패 += 1
                                continue
                            if 번호 in 기존번호목록:
                                중복 += 1
                                continue
                            성별v  = str(row.get(col_gender, "")).strip() if col_gender != "(사용안함)" else ""
                            나이대v = str(row.get(col_age,   "")).strip() if col_age    != "(사용안함)" else ""
                            메모v   = str(row.get(col_memo,  "")).strip() if col_memo   != "(사용안함)" else ""
                            고객_추가(이름, 번호, 성별v, 나이대v, 메모v)
                            기존번호목록.append(번호)
                            성공 += 1
                            진행바.progress((i + 1) / len(df_upload))

                        st.success(f"가져오기 완료! ✅ 등록: {성공}명  |  ⚠️ 중복 건너뜀: {중복}명  |  ❌ 실패: {실패}명")
                        st.rerun()

            else:  # 시술 이력
                col1, col2 = st.columns(2)
                with col1:
                    col_name  = 컬럼선택("고객명 컬럼 *", ["고객명", "이름", "성함"])
                    col_date  = 컬럼선택("방문일자 컬럼 *", ["방문일자", "날짜", "방문날짜"])
                    col_type  = 컬럼선택("시술종류 컬럼 *", ["시술종류", "시술", "서비스"])
                with col2:
                    col_prod  = 컬럼선택("사용제품 컬럼", ["사용제품", "제품"])
                    col_price = 컬럼선택("단가 컬럼 *", ["단가", "금액", "가격", "비용"])
                    col_memo  = 컬럼선택("메모 컬럼", ["메모", "특이사항"])

                if st.button("시술 이력 가져오기", type="primary", use_container_width=True):
                    필수 = [col_name, col_date, col_type, col_price]
                    if "(사용안함)" in 필수:
                        st.error("고객명, 방문일자, 시술종류, 단가 컬럼은 반드시 선택해야 합니다.")
                    else:
                        기존고객df = 고객_불러오기()
                        if 기존고객df.empty:
                            st.error("먼저 고객 명단을 등록(또는 가져오기)해주세요.")
                        else:
                            고객명_to_ID = dict(zip(기존고객df["고객명"], 기존고객df["고객ID"]))
                            성공, 실패_이름없음, 실패_기타 = 0, 0, 0
                            진행바 = st.progress(0)

                            for i, row in df_upload.iterrows():
                                이름  = str(row.get(col_name,  "")).strip()
                                날짜  = str(row.get(col_date,  "")).strip()
                                시술  = str(row.get(col_type,  "")).strip()
                                가격  = str(row.get(col_price, "")).strip().replace(",", "").replace("원", "")
                                제품  = str(row.get(col_prod,  "")).strip() if col_prod  != "(사용안함)" else ""
                                메모v = str(row.get(col_memo,  "")).strip() if col_memo  != "(사용안함)" else ""

                                if 이름 not in 고객명_to_ID:
                                    실패_이름없음 += 1
                                    continue
                                try:
                                    날짜obj = pd.to_datetime(날짜).date()
                                    가격int = int(float(가격)) if 가격 else 0
                                except:
                                    실패_기타 += 1
                                    continue

                                시술이력_추가(고객명_to_ID[이름], 이름, 날짜obj, 시술, 제품, 가격int, 메모v)
                                성공 += 1
                                진행바.progress((i + 1) / len(df_upload))

                            msg = f"가져오기 완료! ✅ 등록: {성공}건"
                            if 실패_이름없음:
                                msg += f"  |  ⚠️ 고객 없음(등록 필요): {실패_이름없음}건"
                            if 실패_기타:
                                msg += f"  |  ❌ 형식오류: {실패_기타}건"
                            st.success(msg)
                            st.rerun()


# ════════════════════════════════════════════
# 탭9: 예약 관리
# ════════════════════════════════════════════
with 탭9:
    st.subheader("📅 예약 관리")

    df_c   = 고객_불러오기()
    df_rsv = 예약_불러오기()
    시술목록  = 시술종류_불러오기()

    # ── 캘린더 뷰 ──
    st.subheader("예약 캘린더")
    st.caption("🔵 예약  🟢 완료  🔴 취소")

    # 연도/월 선택
    오늘 = date.today()
    col_y, col_m, _ = st.columns([1, 1, 3])
    with col_y:
        선택연도cal = st.selectbox("연도", list(range(오늘.year - 1, 오늘.year + 3)), index=1, key="cal_year")
    with col_m:
        선택월cal = st.selectbox("월", list(range(1, 13)), index=오늘.month - 1,
                               format_func=lambda x: f"{x}월", key="cal_month")

    # 해당 월의 예약 필터
    월prefix = f"{선택연도cal}-{선택월cal:02d}"
    월예약 = df_rsv[df_rsv["예약일"].str.startswith(월prefix)].copy() if not df_rsv.empty else pd.DataFrame()

    # 날짜별 예약 dict 생성
    날짜별예약 = {}
    if not 월예약.empty:
        for _, r in 월예약.iterrows():
            d = str(r["예약일"])
            날짜별예약.setdefault(d, []).append(r)

    # 캘린더 그리드 출력
    요일헤더 = ["월", "화", "수", "목", "금", "토", "일"]
    cols_h = st.columns(7)
    for i, 요일 in enumerate(요일헤더):
        색 = "#FF4B4B" if 요일 == "일" else "#4B7BFF" if 요일 == "토" else "#333"
        cols_h[i].markdown(f"<div style='text-align:center;font-weight:bold;color:{색}'>{요일}</div>", unsafe_allow_html=True)

    # 월 첫날 요일(월=0) 및 전체 날짜 계산
    첫날요일, 총일수 = cal_module.monthrange(선택연도cal, 선택월cal)
    칸목록 = [None] * 첫날요일 + list(range(1, 총일수 + 1))
    나머지 = (7 - len(칸목록) % 7) % 7
    칸목록 += [None] * 나머지

    상태이모지 = {"예약": "🔵", "완료": "🟢", "취소": "🔴"}

    for 주idx in range(len(칸목록) // 7):
        주칸 = st.columns(7)
        for 요일idx in range(7):
            일 = 칸목록[주idx * 7 + 요일idx]
            with 주칸[요일idx]:
                if 일 is None:
                    st.markdown("<div style='min-height:70px'></div>", unsafe_allow_html=True)
                else:
                    날짜key = f"{선택연도cal}-{선택월cal:02d}-{일:02d}"
                    오늘강조 = "background:#FFF3CD;border-radius:6px;padding:2px;" if 날짜key == str(오늘) else ""
                    요일색 = "#FF4B4B" if 요일idx == 6 else "#4B7BFF" if 요일idx == 5 else "#333"
                    st.markdown(
                        f"<div style='text-align:center;font-weight:bold;color:{요일색};{오늘강조}'>{일}</div>",
                        unsafe_allow_html=True
                    )
                    if 날짜key in 날짜별예약:
                        for r in 날짜별예약[날짜key]:
                            이모지 = 상태이모지.get(r["상태"], "🔵")
                            st.markdown(
                                f"<div style='font-size:11px;background:#EEF4FF;border-radius:4px;padding:2px 4px;margin:1px 0;overflow:hidden'>"
                                f"{이모지} {r['예약시간'][:5]} {r['고객명']}</div>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("<div style='min-height:40px'></div>", unsafe_allow_html=True)

    st.divider()

    # 이번 달 예약 요약 테이블
    if not 월예약.empty:
        st.markdown(f"**{선택연도cal}년 {선택월cal}월 예약 현황 ({len(월예약)}건)**")
        st.dataframe(
            월예약[["예약일", "예약시간", "고객명", "시술종류", "상태", "메모"]].sort_values(["예약일", "예약시간"]),
            use_container_width=True, hide_index=True,
        )

    st.divider()

    # ── 예약 등록 ──
    st.subheader("신규 예약 등록")

    if df_c.empty:
        st.warning("먼저 고객 등록 탭에서 고객을 등록해주세요.")
    else:
        검색어rsv = st.text_input("고객 이름 검색", placeholder="이름 입력", key="예약검색")
        필터rsv = df_c[df_c["고객명"].str.contains(검색어rsv.strip(), na=False)] if 검색어rsv.strip() else df_c

        if not 필터rsv.empty:
            고객옵션rsv = {
                f"{r['고객명']} ({r['고객ID']})": (r["고객ID"], r["고객명"])
                for _, r in 필터rsv.iterrows()
            }
            with st.form("예약등록폼", clear_on_submit=True):
                선택rsv = st.selectbox("고객 선택 *", list(고객옵션rsv.keys()))
                col1, col2 = st.columns(2)
                with col1:
                    예약일 = st.date_input("예약 날짜 *", value=date.today())
                    시술rsv = st.selectbox("시술 종류 *", 시술목록)
                with col2:
                    시간옵션 = [f"{h:02d}:{m:02d}" for h in range(9, 21) for m in (0, 30)]
                    예약시간 = st.selectbox("예약 시간 *", 시간옵션, index=시간옵션.index("10:00"))
                    메모rsv = st.text_input("메모", placeholder="특이사항 등")
                등록rsv = st.form_submit_button("예약 등록", type="primary", use_container_width=True)

            if 등록rsv:
                고객ID_rsv, 고객명_rsv = 고객옵션rsv[선택rsv]
                예약_추가(고객ID_rsv, 고객명_rsv, 예약일, 예약시간, 시술rsv, 메모rsv)
                st.success(f"'{고객명_rsv}' 님 {예약일} {예약시간} 예약이 등록되었습니다!")
                st.rerun()

    st.divider()

    # ── 예약 목록 및 수정/삭제 ──
    st.subheader("예약 목록 수정 / 삭제")

    df_rsv2 = 예약_불러오기()
    if df_rsv2.empty:
        st.info("등록된 예약이 없습니다.")
    else:
        # 필터
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            필터상태 = st.multiselect("상태 필터", ["예약", "완료", "취소"], default=["예약"])
        with col_f2:
            검색rsv2 = st.text_input("고객명 검색", key="예약목록검색")

        보기df = df_rsv2.copy()
        if 필터상태:
            보기df = 보기df[보기df["상태"].isin(필터상태)]
        if 검색rsv2.strip():
            보기df = 보기df[보기df["고객명"].str.contains(검색rsv2.strip(), na=False)]

        st.dataframe(
            보기df[["예약ID", "예약일", "예약시간", "고객명", "시술종류", "상태", "메모"]],
            use_container_width=True, hide_index=True,
        )
        st.caption(f"총 {len(보기df)}건")

        st.divider()
        st.subheader("예약 수정 / 삭제")

        if not df_rsv2.empty:
            예약옵션 = {
                f"{r['예약ID']} | {r['예약일']} {r['예약시간']} | {r['고객명']} | {r['상태']}": r["예약ID"]
                for _, r in df_rsv2.iterrows()
            }
            선택예약라벨 = st.selectbox("수정/삭제할 예약 선택", list(예약옵션.keys()))
            선택예약ID  = 예약옵션[선택예약라벨]
            원본rsv     = df_rsv2[df_rsv2["예약ID"] == 선택예약ID].iloc[0]

            with st.form("예약수정폼"):
                st.caption(f"예약ID: {선택예약ID}  |  고객: {원본rsv['고객명']}")
                col1, col2 = st.columns(2)
                with col1:
                    수정_예약일 = st.date_input(
                        "예약 날짜",
                        value=datetime.strptime(str(원본rsv["예약일"])[:10], "%Y-%m-%d").date(),
                    )
                    시간옵션2  = [f"{h:02d}:{m:02d}" for h in range(9, 21) for m in (0, 30)]
                    현재시간   = str(원본rsv["예약시간"])[:5]
                    시간idx    = 시간옵션2.index(현재시간) if 현재시간 in 시간옵션2 else 0
                    수정_시간  = st.selectbox("예약 시간", 시간옵션2, index=시간idx)
                with col2:
                    현재시술rsv   = str(원본rsv["시술종류"])
                    수정_시술목록 = 시술목록 if 현재시술rsv in 시술목록 else [현재시술rsv] + 시술목록
                    수정_시술     = st.selectbox("시술 종류", 수정_시술목록, index=수정_시술목록.index(현재시술rsv))
                    수정_상태     = st.selectbox("상태", ["예약", "완료", "취소"],
                                               index=["예약", "완료", "취소"].index(원본rsv["상태"]))
                수정_메모rsv = st.text_input("메모", value=str(원본rsv["메모"]) if pd.notna(원본rsv["메모"]) else "")

                col_저장, col_삭제 = st.columns(2)
                수정rsv저장 = col_저장.form_submit_button("수정 저장", type="primary", use_container_width=True)
                삭제rsv확인 = col_삭제.form_submit_button("예약 삭제", type="secondary", use_container_width=True)

            if 수정rsv저장:
                예약_수정(선택예약ID, 수정_예약일, 수정_시간, 수정_시술, 수정_메모rsv, 수정_상태)
                st.success(f"{선택예약ID} 예약이 수정되었습니다!")
                st.rerun()

            if 삭제rsv확인:
                예약_삭제(선택예약ID)
                st.success(f"{선택예약ID} 예약이 삭제되었습니다.")
                st.rerun()
