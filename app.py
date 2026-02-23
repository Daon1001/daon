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
    business_type = st.text_input("업태 (
