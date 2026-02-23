import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="기업부설연구소 연구과제 추출기", page_icon="🏢")

# 1. API 키 연결
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ 비밀 금고(Secrets)에서 API 키를 찾을 수 없습니다.")
    st.stop()

# 2. 모델 설정
available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
target_model_name = "gemini-1.5-flash" if "gemini-1.5-flash" in available_models else (available_models[0] if available_models else "")

if not target_model_name:
    st.error("⚠️ AI 모델 연결 실패")
    st.stop()

model = genai.GenerativeModel(target_model_name)

# 3. 화면 UI 구성
st.title("🏢 기업부설연구소 연구과제 추출기")
st.info(f"💡 현재 엔진: **{target_model_name}** | 최적의 연구과제가 나올 때까지 반복 검색이 가능합니다.")

# 세션 상태 초기화 (연구과제 누적용)
if 'research_topics' not in st.session_state:
    st.session_state.research_topics = ""

uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

st.write("⌨️ **직접 입력**")
col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("업태", value="제조업")
with col2:
    business_item = st.text_input("종목")

# 4. 분석 함수 정의
def generate_rnd_topics(is_more=False):
    with st.spinner("AI가 새로운 연구과제를 탐색 중입니다..."):
        try:
            variation = "기존과 다른 새로운 기술적 관점에서" if is_more else ""
            
            prompt = f"""
            중소기업 연구소 설립 전문가로서 다음 기업의 KOITA 인정용 연구과제 3가지를 {variation} 제안해 주세요.
            단순 유지보수가 아닌 혁신적인 '신제품 개발'이나 '공정 혁신' 위주로 작성하세요.
            
            [출력 양식]
            * **분류:** (제품개발/공정혁신/핵심부품국산화 등)
            * **연구과제명:** (전문적이고 학술적인 명칭)
            * **연구 목표 및 기대효과:** (상세 기술 내용 포함)
            * **종목 연관성:** (논리적 근거)
            """
            
            if uploaded_file:
                if uploaded_file.name.lower().endswith('.pdf'):
                    content = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}, prompt]
                else:
                    content = [Image.open(uploaded_file), prompt]
                response = model.generate_content(content)
            else:
                response = model.generate_content(f"{prompt}\n업태:{business_type}, 종목:{business_item}")
            
            if is_more:
                st.session_state.research_topics += "\n\n" + "---" * 10 + "\n\n" + response.text
            else:
                st.session_state.research_topics = response.text
                
        except Exception as e:
            st.error(f"오류: {e}")

# 버튼 배치
btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("🚀 연구과제 분석하기", use_container_width=True):
        generate_rnd_topics(is_more=False)

with btn_col2:
    if st.session_state.research_topics:
        if st.button("➕ 다른 연구과제 더 보기", use_container_width=True):
            generate_rnd_topics(is_more=True)

# 5. 결과 출력
if st.session_state.research_topics:
    st.success("✅ 분석된 연구과제 리스트")
    st.markdown(st.session_state.research_topics)
    
    # 서류 안내
    with st.expander("📋 연구소 설립 필수 준비 서류 (클릭하여 확인)"):
        st.warning("연구과제 수행 및 연구소 설립을 위해 아래 서류를 준비해 주세요.")
        st.markdown("""
        **1. 도면 및 사진:** 회사 전체도면, 연구소내도면, 현판사진(가로/세로/두께 포함), 내부사진(여러장)
        **2. 기업 서류:** 조직도, 재무제표, 중소기업확인서
        **3. 인적 서류:** 졸업증명서, 자격증, 주민번호, 핸드폰, 이메일, 4대보험 가입자 명부
        """)
