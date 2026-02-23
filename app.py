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

# 2. 사용 가능한 모든 모델 이름 강제 수집 (에러 원인 파악용)
available_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name.replace('models/', ''))
except Exception as e:
    st.error(f"⚠️ 구글 AI 서버 통신 오류: {e}")
    st.stop()

# 3. 가장 똑똑한 최신 모델부터 순서대로 매칭 시도
target_model_name = ""
for preferred in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro-vision', 'gemini-pro']:
    if preferred in available_models:
        target_model_name = preferred
        break

# 목록에 지정한 이름이 없으면 첫 번째로 검색된 아무 모델이나 강제 할당
if not target_model_name and available_models:
    target_model_name = available_models[0]

# 모델이 아예 0개라면 시스템 상태 화면에 출력
if not target_model_name:
    st.error(f"⚠️ 연결 가능한 AI 모델이 없습니다.\n- 감지된 모델 목록: {available_models}\n- 구글 AI 스튜디오에서 API 키 상태를 확인해 주세요.")
    st.stop()

model = genai.GenerativeModel(target_model_name)

# 4. 화면 UI 구성
st.title("🏢 기업부설연구소 R&D 주제 추출기")
st.info(f"💡 현재 연결된 AI 엔진: **{target_model_name}**")
st.markdown("---")
st.write("사업자등록증 **이미지 또는 PDF 파일**을 첨부하거나, 업태와 종목을 텍스트로 입력하세요.")

uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

st.markdown("---")
st.write("⌨️ **또는 직접 텍스트로 입력**")
col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("업태 (예: 제조업)")
with col2:
    business_item = st.text_input("종목 (예: 금속가공, 소프트웨어 개발)")

# 5. 실행 로직
if st.button("🚀 맞춤형 R&D 주제 도출하기"):
    with st.spinner("AI가 데이터를 분석 중입니다... (약 10초 소요)"):
        try:
            if uploaded_file is not None:
                prompt = """
                당신은 중소기업 연구소 설립 전문 컨설턴트입니다.
                첨부된 사업자등록증(이미지 또는 PDF)에서 '업태'와 '종목'을 찾아낸 뒤, 
                한국산업기술진흥협회(KOITA) 기업부설연구소 설립 요건에 부합하는 R&D 주제 3가지를 제안해 주세요.
                
                [출력 양식]
                * **📌 파악된 기업 정보:** (업태: OO / 종목: OO)
                * **연구 주제명:** (전문적이고 직관적인 명칭)
                * **연구 목표:** (달성하고자 하는 구체적 목표)
                * **기대 효과:** (원가 절감, 생산성 향상 등)
                * **종목 연관성:** (논리적 연결성)
                """
                
                if uploaded_file.name.lower().endswith('.pdf'):
                    if '1.5' not in target_model_name:
                        st.warning(f"⚠️ 현재 연결된 엔진({target_model_name})은 PDF 분석을 지원하지 않습니다. 이미지 파일(JPG/PNG)을 올려주세요.")
                    else:
                        st.info("📄 PDF 문서를 스캔하고 있습니다...")
                        pdf_data = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                        response = model.generate_content([prompt, pdf_data])
                        st.success("파일 분석 및 맞춤형 주제 도출 완료!")
                        st.markdown(response.text)
                else:
                    st.info("🖼️ 이미지를 스캔하고 있습니다...")
                    image = Image.open(uploaded_file)
                    st.image(image, caption="업로드된 사업자등록증", use_container_width=True)
                    response = model.generate_content([prompt, image])
                    st.success("파일 분석 및 맞춤형 주제 도출 완료!")
                    st.markdown(response.text)

            elif business_item:
                prompt = f"""
                당신은 중소기업 연구소 설립 전문 컨설턴트입니다.
                다음 기업의 한국산업기술진흥협회(KOITA) 기업부설연구소 설립 요건에 부합하는 R&D 주제 3가지를 제안해 주세요.
                - 업태: {business_type}
                - 종목: {business_item}
                
                [출력 양식]
                * **연구 주제명:** (전문적이고 직관적인 명칭)
                * **연구 목표:** (달성하고자 하는 구체적 목표)
                * **기대 효과:** (원가 절감, 생산성 향상 등)
                * **종목 연관성:** (논리적 연결성)
                """
                response = model.generate_content(prompt)
                st.success("텍스트 분석 및 도출 완료!")
                st.markdown(response.text)
                
            else:
                st.warning("⚠️ 파일을 업로드하거나, 종목을 텍스트로 입력해 주세요.")
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
