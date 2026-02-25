import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# PDF 처리를 위한 라이브러리
try:
    from pdf2image import convert_from_bytes
except ImportError:
    pass

# --- 0. 페이지 설정 ---
st.set_page_config(page_title="벤처인증 AI 마스터 컨설턴트", layout="wide")

# --- [강력 보안 로직] 허가된 이메일 명단 (화이트리스트) ---
# 컨설턴트님이 허용할 사용자들의 이메일을 이 리스트에 추가하세요.
ALLOWED_EMAILS = [
    "school_house@naver.com", # 본인
    "test@naver.com",   # 테스트용
    "daon@daon.com"     # 업체용 예시
]

MY_CONTACT = "010-9254-1128"

st.sidebar.title("🔐 사용자 인증")
user_email = st.sidebar.text_input("승인된 이메일 주소를 입력하세요")

# 이메일 주소가 명단에 있는지 확인
if not user_email or user_email not in ALLOWED_EMAILS:
    st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")
    st.error(f"""
    ### 🔒 미등록 사용자 안내
    입력하신 **[{user_email}]** 계정은 이용 권한이 등록되지 않았습니다.  
    서비스 이용을 원하시면 임원근 컨설턴트에게 이메일 등록을 요청해 주세요.
    
    **📞 문의: {MY_CONTACT}**
    """)
    st.stop() # 인증 실패 시 하단 로직 실행 안 됨

# --- 1. [인증 성공 시] 동적 모델 할당 로직 ---
try:
    API_KEY = st.secrets["gemini_api_key"] 
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ 비밀 금고(Secrets)에서 API 키를 찾을 수 없습니다.")
    st.stop()

available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
except Exception as e:
    st.error(f"⚠️ 구글 AI 서버 통신 오류: {e}")
    st.stop()

target_model_name = ""
for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision', 'gemini-pro']:
    if preferred in available_models:
        target_model_name = preferred
        break

if not target_model_name and available_models:
    target_model_name = available_models[0]

model = genai.GenerativeModel(target_model_name)
st.sidebar.success(f"✅ 인증 완료: {user_email}")
st.title("🏛️ 벤처인증 통합 컨설팅 대시보드")

# --- 2. UI 레이아웃 ---
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
            except Exception as e:
                st.error(f"PDF 변환 오류: {e}")
        else:
            analysis_image = Image.open(uploaded_file)
        
        st.warning("🔔 **벤처인증 신청 필수 서류 9가지**")
        st.markdown("""
        * ✅ **사업자등록증** | 📋 **법인등기부등본** | 📋 **부가가치세표준증명원**
        * 📋 **재무제표(3년)** | 📋 **고용보험 명부** | 📋 **4대보험 명부**
        * 📋 **대표자 자격득실확인서** | 📋 **주주명부** | 📋 **연구개발인정서**
        """)
        
        if st.button("AI 기술 주제 추천받기"):
            with st.spinner('분석 중...'):
                prompt = "사업자등록증의 종목을 분석하여 벤처인증용 혁신 기술 주제 3개를 전문적인 제목으로 제안해줘."
                response = model.generate_content([prompt, analysis_image])
                st.session_state.suggestions = response.text
                
    if 'suggestions' in st.session_state:
        st.success(st.session_state.suggestions)

with col2:
    st.subheader("2️⃣ 리포트 생성")
    selected_topic = st.text_input("신청기술명 입력:", placeholder="기술명을 입력하거나 왼쪽에서 복사하세요.")
    
    if st.button("마스터 리포트 생성 🚀", type="primary"):
        if not selected_topic:
            st.warning("기술명을 입력해 주세요.")
        else:
            with st.spinner('베테랑 컨설턴트의 시각으로 생성 중...'):
                form_prompt = f"""
                신청기술 [{selected_topic}]에 대해 다음 11개 항목 리포트를 작성하세요. 
                각 항목은 700자 내외의 풍부한 분량과 전문적인 문체를 사용하세요.
                ### [1. 신청기술 요약 및 표준 양식] (V자 양식 포함)
                ### [2. 개발배경 및 원인분석]
                ### [3. 경쟁력 확보방안]
                ### [4. 추진경과 및 향후 계획]
                ### [5. 목표시장 및 고객정의]
                ### [6. 경쟁사 분석 및 우위성]
                ### [7. 시장진입 및 확대전략 - 추진경과]
                ### [8. 시장진입 및 확대전략 - 향후계획]
                ### [9. 지식재산권 및 특허 전략]
                ### [10. 자금조달 계획의 구체적 방안]
                ### [11. 연계 가능 정책자금 추천]
                """
                try:
                    response = model.generate_content([form_prompt, analysis_image]) if analysis_image else model.generate_content(form_prompt)
                    report_text = response.text
                    sections = report_text.split('### ')
                    st.session_state.report_sections = [s for s in sections if s.strip()]
                except Exception as e:
                    st.error(f"오류: {e}")

# --- 3. 결과 출력 ---
st.divider()
if 'report_sections' in st.session_state:
    st.subheader("📄 항목별 상세 컨설팅 리포트")
    full_report = "\n\n".join(st.session_state.report_sections)
    st.download_button("전체 리포트 다운로드(.txt)", full_report, file_name="venture_master_report.txt")

    for section in st.session_state.report_sections:
        lines = section.split('\n')
        title = lines[0].strip('[] ')
        content = '\n'.join(lines[1:]).strip()
        with st.expander(f"📌 {title}", expanded=False):
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 25px; border-radius: 12px; line-height: 1.9; border-left: 6px solid #007bff;'>{content.replace('\n', '<br>')}</div>", unsafe_allow_html=True)
