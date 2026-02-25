import streamlit as st
from streamlit_google_auth import Authenticate
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- [보안 설정] 구글 인증 정보 입력 ---
# 발급받으신 정보를 아래 따옴표 안에 넣어주세요.
GOOGLE_CLIENT_ID = "여기에_복사한_클라이언트_ID_붙여넣기"
GOOGLE_CLIENT_SECRET = "여기에_복사한_비밀번호_붙여넣기"

# --- [관리 설정] 승인된 이메일 목록 ---
ALLOWED_EMAILS = [
    "incheon00@gmail.com",  # 본인 메일 반드시 포함
    "daon@example.com"  # 추가 허용 메일
]
MY_CONTACT = "010-9254-1128"

# --- 0. 구글 인증 객체 생성 ---
authenticator = Authenticate(
    secret_key='venture_master_key',
    cookie_name='venture_auth_cookie',
    cookie_key='auth_v1',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_uri='http://localhost:8501', # 배포 후에는 실제 도메인으로 변경 필요
)

# 로그인 상태 체크 및 로그인 버튼 표시
authenticator.check_authentification()
authenticator.login()

# --- [로그인 성공 시 실행 로직] ---
if st.session_state['connected']:
    user_info = st.session_state['user_info']
    user_email = user_info.get('email')

    # 화이트리스트 검증
    if user_email not in ALLOWED_EMAILS:
        st.error(f"🔒 [{user_email}]님은 등록되지 않은 계정입니다. 임원근 컨설턴트({MY_CONTACT})에게 등록을 요청하세요.")
        if st.button("로그아웃"):
            authenticator.logout()
        st.stop()

    # --- 메인 대시보드 시작 ---
    st.set_page_config(page_title="벤처인증 마스터", layout="wide")
    st.sidebar.success(f"👤 {user_info.get('name')}님 환영합니다!")
    if st.sidebar.button("로그아웃"):
        authenticator.logout()

    # 1. AI 모델 할당
    try:
        API_KEY = st.secrets["gemini_api_key"] 
        genai.configure(api_key=API_KEY)
    except Exception:
        st.error("⚠️ Secrets에서 gemini_api_key를 찾을 수 없습니다.")
        st.stop()

    model = genai.GenerativeModel('gemini-1.5-flash')
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

    # 2. UI 레이아웃 (기존 로직 그대로 통합)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1️⃣ 분석 및 서류 가이드")
        uploaded_file = st.file_uploader("사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "png", "jpeg", "pdf"])
        analysis_image = None
        if uploaded_file:
            if uploaded_file.type == "application/pdf":
                try:
                    pages = convert_from_bytes(uploaded_file.read())
                    if pages: analysis_image = pages[0]
                except Exception as e: st.error(f"PDF 변환 오류: {e}")
            else:
                analysis_image = Image.open(uploaded_file)
            
            st.warning("🔔 **벤처인증 필수 서류 9가지 안내**")
            st.markdown("* ✅ **사업자등록증** | 📋 **법인등기부등본** | 📋 **재무제표** | 📋 **주주명부** 등")
            
            if st.button("AI 기술 주제 추천받기"):
                with st.spinner('분석 중...'):
                    prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 제안해줘."
                    response = model.generate_content([prompt, analysis_image])
                    st.session_state.suggestions = response.text
        if 'suggestions' in st.session_state: st.success(st.session_state.suggestions)

    with col2:
        st.subheader("2️⃣ 리포트 생성")
        selected_topic = st.text_input("신청기술명 입력:")
        if st.button("마스터 리포트 생성 🚀", type="primary"):
            with st.spinner('생성 중...'):
                form_prompt = f"[{selected_topic}] 기술에 대해 11개 항목 리포트를 700자씩 작성해줘."
                # ... (이전과 동일한 11개 항목 리포트 프롬프트)
                response = model.generate_content([form_prompt, analysis_image]) if analysis_image else model.generate_content(form_prompt)
                report_text = response.text
                sections = report_text.split('### ')
                st.session_state.report_sections = [s for s in sections if s.strip()]

    # 3. 결과 출력 (드롭박스)
    st.divider()
    if 'report_sections' in st.session_state:
        for section in st.session_state.report_sections:
            lines = section.split('\n')
            title = lines[0].strip('[] ')
            content = '\n'.join(lines[1:]).strip()
            with st.expander(f"📌 {title}"):
                st.markdown(f"<div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)

else:
    # 로그인 전 화면
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.info("💡 서비스를 이용하시려면 사이드바의 [Google로 로그인] 버튼을 눌러주세요.")
