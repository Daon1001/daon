import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="R&D 주제 추출기", page_icon="🏢")

# 1. API 키 연결
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("⚠️ 비밀 금고(Secrets)에서 API 키를 찾을 수 없습니다.")
    st.stop()

# 2. 사용 가능한 모델 자동 탐색
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

# 3. 화면 UI 구성
st.title("🏢 기업부설연구소 R&D 주제 추출기")
st.info(f"💡 현재 연결된 AI 엔진: **{target_model_name}**")
st.markdown("---")
st.write("사업자등록증 **이미지 또는 PDF 파일**을 첨부하거나, 직접 텍스트를 입력하세요.")

uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

st.markdown("---")
st.write("⌨️ **또는 직접 텍스트로 입력**")
col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("업태 (예: 제조업)")
with col2:
    business_item = st.text_input("종목 (예: 금속가공)")

# 4. 실행 로직
if st.button("🚀 맞춤형 R&D 주제 도출하기"):
    if uploaded_file is None and not business_item:
        st.warning("⚠️ 파일을 업로드하거나 종목을 입력해 주세요.")
    else:
        with st.spinner("AI가 데이터를 분석 중입니다..."):
            try:
                prompt = """
                당신은 중소기업 연구소 설립 전문 컨설턴트입니다.
                첨부된 자료에서 '업태'와 '종목'을 찾아낸 뒤, 
                한국산업기술진흥협회(KOITA) 기업부설연구소 설립 요건에 부합하는 R&D 주제 3가지를 제안해 주세요.
                
                [출력 양식]
                * **📌 파악된 기업 정보:** (업태: OO / 종목: OO)
                * **연구 주제명:** (전문적이고 직관적인 명칭)
                * **연구 목표:** (달성하고자 하는 구체적 목표)
                * **기대 효과:** (원가 절감, 생산성 향상 등)
                * **종목 연관성:** (논리적 연결성)
                """
                
                if uploaded_file is not None:
                    st.write(f"📁 분석 파일: `{uploaded_file.name}`")
                    if uploaded_file.name.lower().endswith('.pdf'):
                        content = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                    else:
                        content = [Image.open(uploaded_file)]
                    response = model.generate_content([prompt] + content)
                else:
                    response = model.generate_content(f"{prompt}\n\n업태: {business_type}\n종목: {business_item}")
                
                # 결과 출력
                st.success("✅ R&D 주제 분석 완료!")
                st.markdown(response.text)
                
                # --- [추가 기능] 서류 안내 섹션 ---
                st.markdown("---")
                st.subheader("📋 연구소 설립 필수 준비 서류 안내")
                st.warning("분석된 주제로 연구소를 설립하기 위해 아래 서류를 준비해 주세요.")
                
                col_doc1, col_doc2 = st.columns(2)
                
                with col_doc1:
                    st.markdown("""
                    **1. 도면 및 사진 자료**
                    * **회사 전체 도면:** 면적 확인용
                    * **연구소 내부 도면:** 연구소 구획 확인
                    * **현판 사진:** **중요!** 가로/세로/두께가 모두 보이도록 측면에서도 촬영
                    * **내부 사진:** 전체 샷, 연구원 자리 샷 등 여러 장
                    
                    **2. 기업 증빙 서류**
                    * **조직도:** 연구소 소속 인원 확인용
                    * **재무제표:** 최근 결산분
                    * **중소기업확인서:** 유효기간 확인 필수
                    """)
                
                with col_doc2:
                    st.markdown("""
                    **3. 인적 자원 서류 (연구원)**
                    * **증명서:** 졸업증명서, 기술자격증
                    * **개인정보:** 주민번호, 휴대폰번호, 이메일
                    * **고용증빙:** 4대보험 가입자 명부
                    
                    **⚠️ 촬영 팁 (현판)**
                    정면 사진뿐만 아니라 **'입체감'**이 느껴지게 대각선 방향에서 가로, 세로, 두께가 다 보이도록 확대해서 찍어야 반려되지 않습니다.
                    """)
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
