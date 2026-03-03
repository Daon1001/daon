import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime, date

# --- [1. 페이지 설정] ---
st.set_page_config(page_title="기업부설연구소 연구과제 추출기", layout="wide", page_icon="🏢")

# --- [2. 사용자 데이터베이스 및 세션 초기화] ---
# 실제 운영 시에는 외부 DB를 써야 하지만, 임시로 세션 내에서 관리자용 로그를 기록합니다.
if 'user_db' not in st.session_state:
    # 초기 관리자 설정 (임원근 대표님)
    st.session_state.user_db = pd.DataFrame([
        {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_month": date.today().month},
    ])

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

# 월간 사용량 제한 설정
MAX_MONTHLY_LIMIT = 10 

# --- [3. 사이드바: 로그인 및 승인 신청] ---
with st.sidebar:
    st.title("🔐 접근 제어")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com").strip().lower()
        col_login, col_req = st.columns(2)
        
        # 로그인 버튼
        if col_login.button("로그인", use_container_width=True, type="primary"):
            user_row = st.session_state.user_db[st.session_state.user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 아직 승인되지 않았습니다. 관리자 승인을 기다려주세요.")
            else:
                st.warning("⚠️ 등록되지 않은 이메일입니다. 승인 신청을 먼저 하세요.")

        # 승인 신청 버튼
        if col_req.button("승인 신청", use_container_width=True):
            if not login_email or "@" not in login_email:
                st.error("올바른 이메일을 입력해주세요.")
            else:
                if login_email not in st.session_state.user_db['email'].values:
                    new_user = {
                        "email": login_email, 
                        "approved": False, 
                        "is_admin": False, 
                        "usage_count": 0,
                        "last_month": date.today().month
                    }
                    st.session_state.user_db = pd.concat([st.session_state.user_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.info("📩 신청 완료! 관리자(incheon00@gmail.com)에게 승인을 요청하세요.")
                else:
                    st.warning("이미 등록(신청)된 이메일입니다.")
    else:
        st.success(f"👤 로그인: {st.session_state.authenticated_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.rerun()

    # 내 사용량 표시
    if st.session_state.authenticated_user:
        st.divider()
        idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
        
        # 월이 바뀌었으면 사용량 초기화
        current_month = date.today().month
        if st.session_state.user_db.at[idx, 'last_month'] != current_month:
            st.session_state.user_db.at[idx, 'usage_count'] = 0
            st.session_state.user_db.at[idx, 'last_month'] = current_month
            
        user_usage = st.session_state.user_db.at[idx, 'usage_count']
        st.caption("🛡️ 나의 월간 사용량")
        st.write(f"**{user_usage} / {MAX_MONTHLY_LIMIT}회**")
        st.progress(min(user_usage / MAX_MONTHLY_LIMIT, 1.0))

# --- [4. 비로그인 시 차단] ---
if st.session_state.authenticated_user is None:
    st.title("🏢 기업부설연구소 연구과제 추출기")
    st.info("💡 왼쪽 사이드바에서 이메일 로그인 후 이용하실 수 있습니다.")
    st.stop()

# --- [5. 관리자 전용 제어판] ---
user_idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
if st.session_state.user_db.at[user_idx, 'is_admin']:
    with st.expander("👑 관리자 전용: 사용자 승인 관리", expanded=False):
        st.write("승인 신청한 사용자 리스트입니다.")
        st.dataframe(st.session_state.user_db, use_container_width=True)
        
        target_email = st.selectbox("승인 처리할 이메일 선택", st.session_state.user_db[st.session_state.user_db['approved'] == False]['email'])
        if st.button("✅ 선택한 사용자 승인하기"):
            st.session_state.user_db.loc[st.session_state.user_db['email'] == target_email, 'approved'] = True
            st.success(f"{target_email}님 승인 완료!")
            st.rerun()

# --- [6. 메인 기능 (기존 로직 통합)] ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Secrets 설정에서 API 키를 확인하세요.")
    st.stop()

st.title("🏢 기업부설연구소 연구과제 추출기")
st.markdown("---")

# 세션 상태 초기화 (연구과제 저장용)
if 'research_topics' not in st.session_state:
    st.session_state.research_topics = ""

uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("업태", value="제조업")
with col2:
    business_item = st.text_input("종목")

# 분석 함수
def generate_rnd_topics(refresh=False):
    current_idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
    
    # 관리자가 아닐 때만 사용량 제한 체크
    if not st.session_state.user_db.at[current_idx, 'is_admin']:
        if st.session_state.user_db.at[current_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
            st.error("🚫 이번 달 사용 횟수(10회)를 모두 소모하셨습니다.")
            return

    with st.spinner("AI가 최적의 연구과제를 도출 중입니다..."):
        try:
            variation = "이전과 중복되지 않는 새로운 기술적 관점에서" if refresh else ""
            prompt = f"""
            중소기업 연구소 설립 전문가로서 다음 기업의 KOITA 인정용 연구과제 3가지를 {variation} 제안해 주세요.
            [출력 양식]
            * **분류:** (유형)
            * **연구과제명:** (전문 명칭)
            * **연구 목표 및 기대효과:** (상세 내용)
            * **종목 연관성:** (논리적 근거)
            """
            
            if uploaded_file:
                # PDF/이미지 처리 (간략화)
                response = model.generate_content([prompt, Image.open(uploaded_file) if uploaded_file.type != "application/pdf" else uploaded_file])
            else:
                response = model.generate_content(f"{prompt}\n업태:{business_type}, 종목:{business_item}")
            
            st.session_state.research_topics = response.text
            # 사용량 1회 증가
            st.session_state.user_db.at[current_idx, 'usage_count'] += 1
            st.rerun()
                
        except Exception as e:
            st.error(f"오류: {e}")

# 버튼 배치
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("🚀 연구과제 분석하기", use_container_width=True):
        generate_rnd_topics(refresh=False)
with btn_col2:
    if st.session_state.research_topics:
        if st.button("🔄 새로운 연구과제 보기", use_container_width=True):
            generate_rnd_topics(refresh=True)

if st.session_state.research_topics:
    st.success("✅ 분석 완료")
    st.markdown(st.session_state.research_topics)
    with st.expander("📋 필수 서류 안내"):
        st.write("도면, 현판사진(두께포함), 내부사진, 조직도, 재무제표, 4대보험명부 등")
