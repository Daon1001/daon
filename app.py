import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. API 키 및 가장 빠르고 똑똑한 최신 비전(Vision) 모델 설정
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 웹 화면 UI 구성
st.set_page_config(page_title="R&D 주제 자동 추출기", page_icon="🏢")
st.title("🏢 기업부설연구소 R&D 주제 추출기")
st.markdown("---")
st.write("사업자등록증 **이미지를 업로드**하거나, 업태와 종목을 직접 텍스트로 입력하세요.")

# 3. 입력 방식 선택 (이미지 파일 업로더 추가)
uploaded_file = st.file_uploader("📸 사업자등록증 이미지 업로드 (JPG, PNG)", type=["jpg", "jpeg", "png"])

st.markdown("---")
st.write("⌨️ **또는 직접 텍스트로 입력**")
col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("업태 (예: 제조업)")
with col2:
    business_item = st.text_input("종목 (예: PVP 창호 프레임 제조)")

# 4. 실행 로직 (이미지와 텍스트 상황 분리)
if st.button("🚀 맞춤형 R&D 주제 도출하기"):
    with st.spinner("AI가 데이터를 분석하고 최적의 주제를 뽑아내고 있습니다... (약 10초 소요)"):
        try:
            if uploaded_file is not None:
                # [기능 1] 이미지가 업로드된 경우: AI가 눈으로 보고 판단
                image = Image.open(uploaded_file)
                st.image(image, caption="업로드된 사업자등록증", use_container_width=True)
                
                prompt = """
                당신은 중소기업 연구소 설립 전문 컨설턴트입니다.
                첨부된 사업자등록증 이미지에서 '업태'와 '종목'을 정확히 찾아낸 뒤, 
                이를 바탕으로 한국산업기술진흥협회(KOITA) 기업부설연구소 설립 요건에 부합하는 R&D 주제 3가지를 제안해 주세요.
                
                [출력 양식]
                * **📌 파악된 기업 정보:** (업태: OO / 종목: OO)
                * **연구 주제명:** (전문적이고 직관적인 명칭)
                * **연구 목표:** (해당 연구를 통해 달성하고자 하는 구체적 목표)
                * **기대 효과:** (원가 절감, 생산성 향상, 매출 증대 등)
                * **종목 연관성:** (해당 종목과 이 연구가 어떻게 논리적으로 연결되는지)
                """
                
                response = model.generate_content([prompt, image])
                st.success("이미지 분석 및 맞춤형 주제 도출 완료!")
                st.markdown(response.text)

            elif business_item:
                # [기능 2] 텍스트만 입력된 경우: 기존과 동일하게 작동
                prompt = f"""
                당신은 중소기업 연구소 설립 전문 컨설턴트입니다.
                다음 기업의 한국산업기술진흥협회(KOITA) 기업부설연구소 설립 요건에 부합하는 R&D 주제 3가지를 제안해 주세요.
                
                - 업태: {business_type}
                - 종목: {business_item}
                
                [출력 양식]
                * **연구 주제명:** (전문적이고 직관적인 명칭)
                * **연구 목표:** (해당 연구를 통해 달성하고자 하는 구체적 목표)
                * **기대 효과:** (원가 절감, 생산성 향상, 매출 증대 등)
                * **종목 연관성:** (해당 종목과 이 연구가 어떻게 논리적으로 연결되는지)
                """
                
                response = model.generate_content(prompt)
                st.success("텍스트 분석 및 도출 완료!")
                st.markdown(response.text)
                
            else:
                # 아무것도 입력하지 않고 버튼을 누른 경우
                st.warning("⚠️ 이미지를 업로드하거나, 종목을 텍스트로 입력해 주세요.")
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
