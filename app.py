import streamlit as st
import google.generativeai as genai

# 1. 스트림릿 비밀금고에서 API 키 불러오기
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

# 2. 가장 안정적인 범용 모델로 설정 변경 (이 부분이 해결책입니다!)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. 웹 화면 UI 구성
st.set_page_config(page_title="R&D 주제 자동 추출기", page_icon="🏢")
st.title("🏢 기업부설연구소 R&D 주제 추출기")
st.markdown("---")
st.write("사업자등록증의 **업태**와 **종목**을 입력하면 심사에 유리한 R&D 주제를 자동으로 제안합니다.")

# 입력 폼
col1, col2 = st.columns(2)
with col1:
    business_type = st.text_input("업태 (예: 제조업, 정보통신업)")
with col2:
    business_item = st.text_input("종목 (예: 금속가공, 소프트웨어 개발)")

# 4. 실행 로직
if st.button("🚀 맞춤형 R&D 주제 도출하기"):
    if business_item:
        with st.spinner("AI가 최적의 R&D 주제를 분석하고 있습니다... (약 10초 소요)"):
            prompt = f"""
            당신은 중소기업 연구소 설립 전문 컨설턴트입니다.
            다음 기업의 한국산업기술진흥협회(KOITA) 기업부설연구소 설립 요건에 부합하는 R&D 주제 3가지를 제안해 주세요.
            
            - 업태: {business_type}
            - 종목: {business_item}
            
            [출력 양식]
            * **연구 주제명:** (전문적이고 직관적인 명칭)
            * **연구 목표:** (달성하고자 하는 구체적 목표)
            * **기대 효과:** (원가 절감, 생산성 향상 등)
            * **종목 연관성:** (해당 종목과 어떻게 연결되는지)
            """
            
            # AI에게 답변 요청 및 에러 방지 처리
            try:
                response = model.generate_content(prompt)
                st.success("분석이 완료되었습니다!")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
    else:
        st.warning("⚠️ 종목을 반드시 입력해 주세요.")

