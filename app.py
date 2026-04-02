import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import uuid

# ─────────────────────────────────────────────
# 더미 데이터 생성
# ─────────────────────────────────────────────

random.seed(42)
np.random.seed(42)

INSTRUMENTS = ["드럼", "베이스", "기타", "트럼펫", "피아노"]
GENRES = ["pop", "rock", "jazz", "classical", "hiphop"]
REGIONS = ["서울", "경기", "부산", "대구", "광주"]
CHAPTERS = ["실행", "반복", "조건", "연산", "함수"]
ERROR_LABELS = {
    1: "블록 인식 오류", 2: "시작/반복 미사용", 3: "시작 블록 중복", 4: "반복 블록 중복",
    5: "조건-왼쪽 중복", 6: "조건-오른쪽 중복", 7: "조건-else 중복", 8: "else 단독 사용",
    9: "악기 블록 없음", 10: "단계 미초기화",
    11: "스타 저장 없이 실행", 12: "스타 저장 중복", 13: "스타 저장 비어있음", 14: "스타 저장 잘못된 연결"
}

def gen_score():
    a = random.choice([0, 30])
    b = random.choice([0, 10, 20, 40])
    c = random.choice([0, 5, 10, 20, 30])
    return a, b, c, a + b + c

def gen_students(n, class_id):
    rows = []
    for i in range(n):
        uid = f"student-{class_id[-1]}-{i+1:02d}"
        pa, pb, pc, pt = gen_score()
        la, lb, lc, lt = gen_score()
        ca, cb, cc, ct = gen_score()
        oa, ob, oc, ot = gen_score()
        fa, fb, fc, ft = gen_score()
        ach = pt + lt + ct + ot + ft
        errs = random.sample(range(1, 15), k=random.randint(0, 3))
        rows.append({
            "user_id": uid, "class_id": class_id,
            "play_a": pa, "play_b": pb, "play_c": pc, "play_total": pt,
            "loop_a": la, "loop_b": lb, "loop_c": lc, "loop_total": lt,
            "cond_a": ca, "cond_b": cb, "cond_c": cc, "cond_total": ct,
            "op_a": oa, "op_b": ob, "op_c": oc, "op_total": ot,
            "func_a": fa, "func_b": fb, "func_c": fc, "func_total": ft,
            "achievement_score": ach,
            "errors": errs,
            "error_count": len(errs),
            "favorite_instrument": random.choice(INSTRUMENTS),
            "genre": random.choice(GENRES),
            "sex": random.choice(["남", "여"]),
            "age": random.choice(["8", "9", "10", "11", "12"]),
            "region": random.choice(REGIONS),
            "total_play_time_sec": random.randint(300, 3600),
            "total_sessions": random.randint(1, 20),
            "block_count": random.randint(3, 30),
        })
    return pd.DataFrame(rows)

CLASS_IDS = ["class-A", "class-B", "class-C"]
CLASS_NAMES = {"class-A": "3학년 1반", "class-B": "3학년 2반", "class-C": "4학년 1반"}

all_students = pd.concat([gen_students(random.randint(20, 30), cid) for cid in CLASS_IDS], ignore_index=True)

# ─────────────────────────────────────────────
# Streamlit 앱
# ─────────────────────────────────────────────

st.set_page_config(page_title="대시보드", layout="wide")

# 사이드바
st.sidebar.title("대시보드")
dashboard_mode = st.sidebar.radio("대시보드 선택", ["교사용 대시보드", "관리자용 대시보드"])

# ═══════════════════════════════════════════════
# 교사용 대시보드
# ═══════════════════════════════════════════════

if dashboard_mode == "교사용 대시보드":

    st.title("📚 교사용 대시보드")

    # 반 선택
    selected_class = st.sidebar.selectbox("반 선택", CLASS_IDS, format_func=lambda x: CLASS_NAMES[x])
    df = all_students[all_students["class_id"] == selected_class].copy()

    # ── 상단 요약 카드 ──
    st.subheader(f"{CLASS_NAMES[selected_class]} 요약")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("참여 학생 수", f"{len(df)}명")
    col2.metric("반 평균 종합 점수", f"{df['achievement_score'].mean():.0f} / 500")

    other_df = all_students[all_students["class_id"] != selected_class]
    other_avg = other_df["achievement_score"].mean()
    diff = df["achievement_score"].mean() - other_avg
    col3.metric("다른 반 대비", f"{diff:+.0f}점", delta=f"{diff:+.0f}")

    top_inst = df["favorite_instrument"].value_counts().index[0]
    col4.metric("인기 악기", top_inst)

    st.divider()

    # ── 챕터별 반 평균 점수 ──
    st.subheader("챕터별 반 평균 점수")

    chapter_avgs = pd.DataFrame({
        "챕터": CHAPTERS,
        "A (사용 여부)": [df[f"{c}_a"].mean() for c in ["play", "loop", "cond", "op", "func"]],
        "B (구조/다양성)": [df[f"{c}_b"].mean() for c in ["play", "loop", "cond", "op", "func"]],
        "C (응용/심화)": [df[f"{c}_c"].mean() for c in ["play", "loop", "cond", "op", "func"]],
        "총점": [df[f"{c}_total"].mean() for c in ["play", "loop", "cond", "op", "func"]],
    })

    fig_chapter = go.Figure()
    for col_name, color in [("A (사용 여부)", "#7F77DD"), ("B (구조/다양성)", "#1D9E75"), ("C (응용/심화)", "#EF9F27")]:
        fig_chapter.add_trace(go.Bar(
            name=col_name, x=chapter_avgs["챕터"], y=chapter_avgs[col_name],
            marker_color=color
        ))
    fig_chapter.update_layout(barmode="stack", height=350, margin=dict(t=20, b=40),
                              yaxis_title="평균 점수", legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_chapter, use_container_width=True)

    # ── 다른 반 비교 ──
    st.subheader("다른 반과 비교")

    compare_data = []
    for cid in CLASS_IDS:
        cdf = all_students[all_students["class_id"] == cid]
        compare_data.append({
            "반": CLASS_NAMES[cid],
            "실행": cdf["play_total"].mean(),
            "반복": cdf["loop_total"].mean(),
            "조건": cdf["cond_total"].mean(),
            "연산": cdf["op_total"].mean(),
            "함수": cdf["func_total"].mean(),
        })
    compare_df = pd.DataFrame(compare_data)

    fig_compare = go.Figure()
    colors = ["#7F77DD", "#1D9E75", "#EF9F27", "#D85A30", "#D4537E"]
    for i, ch in enumerate(CHAPTERS):
        fig_compare.add_trace(go.Bar(name=ch, x=compare_df["반"], y=compare_df[ch], marker_color=colors[i]))
    fig_compare.update_layout(barmode="group", height=300, margin=dict(t=20, b=40),
                              yaxis_title="평균 점수", legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_compare, use_container_width=True)

    st.divider()

    # ── 부진/우수 학생 ──
    st.subheader("주의 / 우수 학생")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**⚠️ 주의 학생** (3개 이상 챕터 부진)")
        struggling_threshold = 30
        df["struggling_count"] = sum(
            (df[f"{c}_total"] < struggling_threshold).astype(int)
            for c in ["play", "loop", "cond", "op", "func"]
        )
        at_risk = df[df["struggling_count"] >= 3][["user_id", "achievement_score", "struggling_count"]].sort_values("achievement_score")
        if len(at_risk) > 0:
            st.dataframe(at_risk.rename(columns={
                "user_id": "학생 ID", "achievement_score": "종합 점수", "struggling_count": "부진 챕터 수"
            }), hide_index=True, use_container_width=True)
        else:
            st.info("주의 학생이 없습니다.")

    with col_right:
        st.markdown("**🌟 우수 학생** (상위 10%)")
        top_threshold = df["achievement_score"].quantile(0.9)
        top_students = df[df["achievement_score"] >= top_threshold][["user_id", "achievement_score"]].sort_values("achievement_score", ascending=False)
        if len(top_students) > 0:
            st.dataframe(top_students.rename(columns={
                "user_id": "학생 ID", "achievement_score": "종합 점수"
            }), hide_index=True, use_container_width=True)
        else:
            st.info("데이터가 부족합니다.")

    st.divider()

    # ── 학생별 에러케이스 ──
    st.subheader("학생별 에러케이스")

    error_rows = []
    for _, row in df.iterrows():
        for e in row["errors"]:
            error_rows.append({"학생 ID": row["user_id"], "에러 코드": e, "에러 설명": ERROR_LABELS.get(e, "")})
    if error_rows:
        error_df = pd.DataFrame(error_rows)

        col_e1, col_e2 = st.columns([1, 1])
        with col_e1:
            error_count_df = error_df["에러 설명"].value_counts().reset_index()
            error_count_df.columns = ["에러 유형", "발생 횟수"]
            fig_err = px.bar(error_count_df.head(10), x="발생 횟수", y="에러 유형", orientation="h",
                             color_discrete_sequence=["#E24B4A"])
            fig_err.update_layout(height=350, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_err, use_container_width=True)

        with col_e2:
            st.dataframe(error_df, hide_index=True, use_container_width=True, height=350)
    else:
        st.info("에러가 발생하지 않았습니다.")

    st.divider()

    # ── 학생별 A/B/C 점수 상세 ──
    st.subheader("학생별 점수 상세")

    score_cols = ["user_id"]
    for c in ["play", "loop", "cond", "op", "func"]:
        score_cols.extend([f"{c}_a", f"{c}_b", f"{c}_c", f"{c}_total"])
    score_cols.append("achievement_score")

    display_df = df[score_cols].copy()
    display_df.columns = (
        ["학생 ID"] +
        [f"{ch}_{s}" for ch in ["실행", "반복", "조건", "연산", "함수"] for s in ["A", "B", "C", "총점"]] +
        ["종합 점수"]
    )
    st.dataframe(display_df, hide_index=True, use_container_width=True)


# ═══════════════════════════════════════════════
# 관리자용 대시보드
# ═══════════════════════════════════════════════

elif dashboard_mode == "관리자용 대시보드":

    st.title("🔧 관리자용 대시보드")
    df = all_students.copy()

    # 필터
    st.sidebar.subheader("필터")
    sel_region = st.sidebar.multiselect("지역", REGIONS, default=REGIONS)
    sel_age = st.sidebar.multiselect("나이", sorted(df["age"].unique()), default=sorted(df["age"].unique()))
    sel_sex = st.sidebar.multiselect("성별", ["남", "여"], default=["남", "여"])

    df = df[(df["region"].isin(sel_region)) & (df["age"].isin(sel_age)) & (df["sex"].isin(sel_sex))]

    # ── 상단 요약 ──
    st.subheader("전체 요약")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("전체 학생 수", f"{len(df)}명")
    c2.metric("총 세션 수", f"{df['total_sessions'].sum():,}")
    c3.metric("평균 종합 점수", f"{df['achievement_score'].mean():.0f}")
    total_time_hr = df["total_play_time_sec"].sum() / 3600
    c4.metric("총 앱 사용 시간", f"{total_time_hr:.1f}시간")
    c5.metric("평균 에러 수", f"{df['error_count'].mean():.1f}건")

    st.divider()

    # ── 지역별 / 나이별 / 성별 분석 ──
    st.subheader("인구통계별 분석")

    tab1, tab2, tab3 = st.tabs(["지역별", "나이별", "성별"])

    with tab1:
        region_df = df.groupby("region").agg(
            학생수=("user_id", "count"),
            평균점수=("achievement_score", "mean"),
            평균사용시간=("total_play_time_sec", "mean")
        ).reset_index().rename(columns={"region": "지역"})
        region_df["평균사용시간"] = (region_df["평균사용시간"] / 60).round(1)

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            fig = px.bar(region_df, x="지역", y="평균점수", color="지역",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(height=300, margin=dict(t=20, b=40), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col_r2:
            st.dataframe(region_df, hide_index=True, use_container_width=True)

    with tab2:
        age_df = df.groupby("age").agg(
            학생수=("user_id", "count"),
            평균점수=("achievement_score", "mean"),
        ).reset_index().rename(columns={"age": "나이"})

        fig = px.bar(age_df, x="나이", y="평균점수", color="나이",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=300, margin=dict(t=20, b=40), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        sex_df = df.groupby("sex").agg(
            학생수=("user_id", "count"),
            평균점수=("achievement_score", "mean"),
        ).reset_index().rename(columns={"sex": "성별"})

        fig = px.bar(sex_df, x="성별", y="평균점수", color="성별",
                     color_discrete_sequence=["#378ADD", "#D4537E"])
        fig.update_layout(height=300, margin=dict(t=20, b=40), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── 에러케이스 통계 ──
    st.subheader("에러케이스 통계")

    all_errors = []
    for _, row in df.iterrows():
        for e in row["errors"]:
            all_errors.append({"에러 코드": e, "에러 설명": ERROR_LABELS.get(e, "")})

    if all_errors:
        err_df = pd.DataFrame(all_errors)
        err_count = err_df["에러 설명"].value_counts().reset_index()
        err_count.columns = ["에러 유형", "발생 횟수"]

        fig_err = px.bar(err_count, x="발생 횟수", y="에러 유형", orientation="h",
                         color_discrete_sequence=["#E24B4A"])
        fig_err.update_layout(height=400, margin=dict(t=20, b=20), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_err, use_container_width=True)

    st.divider()

    # ── 장르 / 악기 / 블록 사용 빈도 ──
    st.subheader("사용 빈도 분석")

    tab_g, tab_i, tab_b = st.tabs(["장르", "악기", "블록 유형"])

    with tab_g:
        genre_count = df["genre"].value_counts().reset_index()
        genre_count.columns = ["장르", "사용 횟수"]
        fig = px.pie(genre_count, names="장르", values="사용 횟수", hole=0.4,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with tab_i:
        inst_count = df["favorite_instrument"].value_counts().reset_index()
        inst_count.columns = ["악기", "사용 횟수"]
        fig = px.bar(inst_count, x="악기", y="사용 횟수", color="악기",
                     color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_layout(height=350, margin=dict(t=20, b=40), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab_b:
        block_types = []
        for ch in CHAPTERS:
            prefix = {"실행": "play", "반복": "loop", "조건": "cond", "연산": "op", "함수": "func"}[ch]
            has_col = f"has_{prefix}" if f"has_{prefix}" in df.columns else None
            count = (df[f"{prefix}_a"] > 0).sum()
            block_types.append({"블록 유형": ch, "사용 학생 수": count})
        bt_df = pd.DataFrame(block_types)
        fig = px.bar(bt_df, x="블록 유형", y="사용 학생 수", color="블록 유형",
                     color_discrete_sequence=["#7F77DD", "#1D9E75", "#EF9F27", "#D85A30", "#D4537E"])
        fig.update_layout(height=350, margin=dict(t=20, b=40), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── 블록 길이 통계 ──
    st.subheader("세션당 블록 수 통계")

    col_bl1, col_bl2, col_bl3 = st.columns(3)
    col_bl1.metric("평균 블록 수", f"{df['block_count'].mean():.1f}")
    col_bl2.metric("최대 블록 수", f"{df['block_count'].max()}")
    col_bl3.metric("최소 블록 수", f"{df['block_count'].min()}")

    fig_hist = px.histogram(df, x="block_count", nbins=15,
                            color_discrete_sequence=["#534AB7"],
                            labels={"block_count": "블록 수", "count": "학생 수"})
    fig_hist.update_layout(height=300, margin=dict(t=20, b=40))
    st.plotly_chart(fig_hist, use_container_width=True)


# ── 푸터 ──
st.sidebar.divider()
st.sidebar.caption("대시보 프로토타입")
