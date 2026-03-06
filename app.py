"""
수진뷰티 고객 관리 프로그램 (Supabase 버전)
- 데이터는 Supabase 클라우드 DB에 저장됩니다
- 어디서든 URL로 접속 가능합니다
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date

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
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(page_title="수진뷰티 고객 관리", page_icon="💄", layout="wide")
st.title("💄 수진뷰티 고객 관리 시스템")
st.divider()

탭1, 탭2, 탭3, 탭4, 탭5, 탭6, 탭7 = st.tabs([
    "👤 고객 등록",
    "✂️ 시술 이력 등록",
    "🔍 개인별 조회",
    "📊 매출 통계",
    "📋 고객 전체 리스트",
    "⚙️ 시술종류 관리",
    "📱 단체문자",
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
            고객_추가(고객명, 휴대폰번호, 성별, 나이대, 메모)
            st.success(f"'{고객명}' 고객이 등록되었습니다!")
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
