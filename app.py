import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime, date
import io

# --- [1. 페이지 설정 및 초기화] ---
st.set_page_config(page_title="기업부설연구소 연구과제 추출기", layout="wide", page_icon="🏢")

# 관리자 설정 및 사용자 DB 초기화 (세션 내 관리)
if 'user_db' not in st.session_state:
    st.session_state.user_db = pd.DataFrame([
        {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "usage_count": 0, "last_month": date.today().month},
    ])

if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if 'research_topics' not in st.session_state:
    st.session_state.research_topics = ""

# 월간 사용량 제한
MAX_MONTHLY_LIMIT = 10 

# --- [2. 사이드바: 로그인 및 승인 관리] ---
with st.sidebar:
    st.title("🔐 컨설턴트 인증")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com").strip().lower()
        col_login, col_req = st.columns(2)
        
        if col_login.button("로그인", use_container_width=True, type="primary"):
            user_row = st.session_state.user_db[st.session_state.user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 승인 대기 중입니다. 관리자 승인을 기다려주세요.")
            else:
                st.warning("⚠️ 등록되지 않은 이메일입니다. [승인 신청]을 먼저 하세요.")

        if col_req.button("승인 신청", use_container_width=True):
            if "@" not in login_email:
                st.error("올바른 이메일 형식을 입력해주세요.")
            else:
                if login_email not in st.session_state.user_db['email'].values:
                    new_user = {
                        "email": login_email, "approved": False, "is_admin": False, 
                        "usage_count": 0, "last_month": date.today().month
                    }
                    st.session_state.user_db = pd.concat([st.session_state.user_db, pd.DataFrame([new_user])], ignore_index=True)
                    st.info("📩 신청 완료! 관리자에게 승인을 요청하세요.")
                else:
                    st.warning("이미 신청된 이메일입니다.")
    else:
        st.success(f"👤 접속 중: {st.session_state.authenticated_user}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.session_state.research_topics = ""
            st.rerun()

    # 개인별 사용량 표시 및 자동 초기화 로직
    if st.session_state.authenticated_user:
        st.divider()
        idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
        
        current_month = date.today().month
        if st.session_state.user_db.at[idx, 'last_month'] != current_month:
            st.session_state.user_db.at[idx, 'usage_count'] = 0
            st.session_state.user_db.at[idx, 'last_month'] = current_month
            
        u_count = st.session_state.user_db.at[idx, 'usage_count']
        is_admin_user = st.session_state.user_db.at[idx, 'is_admin']
        
        st.caption("🛡️ 월간 사용 현황")
        if is_admin_user:
            st.write("계정 권한: **관리자 (무제한)**")
        else:
            st.write(f"나의 사용량: **{u_count} / {MAX_MONTHLY_LIMIT}**회")
            st.progress(min(u_count / MAX_MONTHLY_LIMIT, 1.0))

# --- [3. 메인 화면 구성] ---
if st.session_state.authenticated_user is None:
    st.title("🏢 기업부설연구소 연구과제 추출기")
    st.info("💡 사이드바에서 이메일 로그인 후 이용 가능합니다.")
    st.stop()

# 관리자 제어판 (incheon00@gmail.com 전용)
user_idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
if st.session_state.user_db.at[user_idx, 'is_admin']:
    with st.expander("👑 [관리자] 사용자 승인 및 현황 관리", expanded=False):
        st.dataframe(st.session_state.user_db, use_container_width=True)
        pending_users = st.session_state.user_db[st.session_state.user_db['approved'] == False]['email'].tolist()
        if pending_users:
            target = st.selectbox("승인할 사용자 선택", pending_users)
            if st.button("✅ 선택한 사용자 승인 완료"):
                st.session_state.user_db.loc[st.session_state.user_db['email'] == target, 'approved'] = True
                st.rerun()
        else:
            st.write("새로운 승인 신청이 없습니다.")

# AI 모델 설정
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Secrets 설정에서 API 키를 확인하세요.")
    st.stop()

st.title("🏢 기업부설연구소 연구과제 추출기")
st.write(f"반갑습니다, **{st.session_state.authenticated_user}** 컨설턴트님.")
st.markdown("---")

# 파일 업로드 및 입력
uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (이미지 안보임 처리됨)", type=["jpg", "jpeg", "png", "pdf"])

col1, col2 = st.columns(2)
with col1:
    biz_type = st.text_input("업태", value="제조업")
with col2:
    biz_item = st.text_input("종목", placeholder="예: PVP 창호 프레임 제조")

# 분석 함수
def analyze_research(refresh=False):
    u_idx = st.session_state.user_db[st.session_state.user_db['email'] == st.session_state.authenticated_user].index[0]
    
    # 관리자가 아닌 경우 사용량 체크
    if not st.session_state.user_db.at[u_idx, 'is_admin']:
        if st.session_state.user_db.at[u_idx, 'usage_count'] >= MAX_MONTHLY_LIMIT:
            st.error("🚫 이번 달 사용 횟수(10회)를 모두 소모하셨습니다.")
            return

    with st.spinner("업종별 실무 기술 스펙트럼을 분석 중입니다..."):
        try:
            variation = "이전과 중복되지 않는 새로운 기술적 관점에서" if refresh else ""
            prompt = f"""
            당신은 20년 경력의 중소기업 기술 컨설팅 전문가입니다. 
            제시된 업태와 종목을 바탕으로, KOITA 연구소 인정에 최적화된 '연구과제' 3가지를 제안하세요.

            **[기술 스펙트럼 확장 가이드라인]**
            1. IT/소프트웨어(AI, 스마트)에만 편중되지 않도록 실무적인 하드웨어 혁신을 포함하세요.
            2. 제조업: 자동화 지그(Jig), 고강도 신소재, 공정 사이클 타임 단축, 부품 국산화, 내구성 향상 표면처리 기술 등.
            3. 유통/서비스: 친환경 패키징, 독자적 물류 하드웨어, 서비스 표준화 기술 등.
            4. {variation} 제안하되 전문 용어를 사용하여 연구계획서에 바로 쓸 수 있게 작성하세요.

            [출력 양식]
            * **분류:** (유형)
            * **연구과제명:** (전문 명칭)
            * **연구 목표 및 기대효과:** (상세 기술 내용)
            * **종목 연관성:** (논리적 근거)
            """
            
            if uploaded_file:
                st.info(f"📁 파일 분석 중: {uploaded_file.name}")
                if uploaded_file.type == "application/pdf":
                    response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}])
                else:
                    response = model.generate_content([prompt, Image.open(uploaded_file)])
            else:
                response = model.generate_content(f"{prompt}\n업태:{biz_type}, 종목:{biz_item}")
            
            st.session_state.research_topics = response.text
            st.session_state.user_db.at[u_idx, 'usage_count'] += 1
            st.rerun()
                
        except Exception as e:
            st.error(f"오류 발생: {e}")

# 버튼 영역
b_col1, b_col2 = st.columns(2)
with b_col1:
    if st.button("🚀 연구과제 분석하기", use_container_width=True, key="main_analyze"):
        analyze_research(refresh=False)
with b_col2:
    if st.session_state.research_topics:
        if st.button("🔄 새로운 연구과제 보기", use_container_width=True, key="refresh_analyze"):
            analyze_research(refresh=True)

# 결과 출력
if st.session_state.research_topics:
    st.success("✅ 분석 완료 (목록은 누적되지 않고 교체됩니다)")
    st.markdown(st.session_state.research_topics)
    
    with st.expander("📋 연구소 설립 필수 준비 서류 (클릭)"):
        st.warning("연구소 설립을 위해 아래 서류를 준비해 주세요.")
        st.markdown("""
        **1. 도면 및 사진:** 회사 전체도면, 연구소내도면, 현판사진(가로/세로/두께 포함), 내부사진(여러장)
        **2. 기업 서류:** 조직도, 재무제표, 중소기업확인서
        **3. 인적 서류:** 졸업증명서, 자격증, 주민번호, 핸드폰, 이메일, 4대보험 가입자 명부
        """)
