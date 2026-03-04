import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime, date
import os
import io

# --- [1. 페이지 설정 및 시스템 초기화] ---
st.set_page_config(page_title="기업부설연구소 연구과제 추출기", layout="wide", page_icon="🏢")

# CSV 데이터베이스 설정
DB_FILE = "users.csv"
MAX_DAILY_LIMIT = 10  # 일일 사용량 한도

def load_db():
    current_date_str = date.today().strftime("%Y-%m-%d")
    
    if not os.path.exists(DB_FILE):
        initial_data = pd.DataFrame([
            {"email": "incheon00@gmail.com", "approved": True, "is_admin": True, "created_at": current_date_str, "usage_count": 0, "last_date": current_date_str},
        ])
        initial_data.to_csv(DB_FILE, index=False)
        return initial_data
    else:
        df = pd.read_csv(DB_FILE)
        changed = False
        
        required_columns = {
            'approved': False,
            'is_admin': False,
            'created_at': current_date_str,
            'usage_count': 0,
            'last_date': current_date_str
        }
        
        for col, default_val in required_columns.items():
            if col not in df.columns:
                df[col] = default_val
                changed = True
                
        if 'last_month' in df.columns:
            df = df.drop(columns=['last_month'])
            changed = True
            
        if changed:
            df.to_csv(DB_FILE, index=False)
            
        return df

def save_db(df):
    df.to_csv(DB_FILE, index=False)

user_db = load_db()

# 세션 초기화
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if 'research_topics' not in st.session_state:
    st.session_state.research_topics = ""

# --- [2. 사이드바: 로그인 및 승인 관리] ---
with st.sidebar:
    st.title("🔐 컨설턴트 인증")
    
    if st.session_state.authenticated_user is None:
        login_email = st.text_input("이메일 입력", placeholder="example@gmail.com").strip().lower()
        col_login, col_req = st.columns(2)
        
        if col_login.button("로그인", use_container_width=True, type="primary"):
            user_row = user_db[user_db['email'] == login_email]
            if not user_row.empty:
                if user_row.iloc[0]['approved']:
                    st.session_state.authenticated_user = login_email
                    st.rerun()
                else:
                    st.error("❌ 승인 대기 중입니다. 관리자에게 문의하세요.")
            else:
                st.warning("⚠️ [승인 신청]을 먼저 하세요.")

        if col_req.button("승인 신청", use_container_width=True):
            if "@" in login_email:
                if login_email not in user_db['email'].values:
                    new_user = pd.DataFrame([{
                        "email": login_email, 
                        "approved": False, 
                        "is_admin": False, 
                        "created_at": date.today().strftime("%Y-%m-%d"),
                        "usage_count": 0, 
                        "last_date": date.today().strftime("%Y-%m-%d")
                    }])
                    user_db = pd.concat([user_db, new_user], ignore_index=True)
                    save_db(user_db)
                    st.info("📩 신청 완료! 관리자에게 승인을 요청하세요.")
                else:
                    st.warning("이미 신청된 이메일입니다.")
            else:
                st.error("이메일 형식을 확인하세요.")
    else:
        st.success(f"👤 {st.session_state.authenticated_user}님")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.authenticated_user = None
            st.session_state.research_topics = ""
            st.rerun()

    if st.session_state.authenticated_user:
        st.divider()
        idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
        
        current_date_str = date.today().strftime("%Y-%m-%d")
        if str(user_db.at[idx, 'last_date']) != current_date_str:
            user_db.at[idx, 'usage_count'] = 0
            user_db.at[idx, 'last_date'] = current_date_str
            save_db(user_db)
            
        u_count = user_db.at[idx, 'usage_count']
        is_admin_user = user_db.at[idx, 'is_admin']
        
        st.caption("🛡️ 일일 사용 현황")
        if is_admin_user:
            st.write("권한: **관리자 (무제한)**")
        else:
            st.write(f"오늘 사용량: **{u_count} / {MAX_DAILY_LIMIT}**회")
            st.progress(min(u_count / MAX_DAILY_LIMIT, 1.0))

# --- [3. 메인 화면 구성 및 API 동적 체크 (대표님 작성 로직 적용)] ---
if st.session_state.authenticated_user is None:
    st.title("🏢 기업부설연구소 연구과제 추출기")
    st.info("💡 사이드바에서 이메일 로그인 후 이용 가능합니다.")
    st.stop()

# 1. [인증 성공 시] 동적 모델 할당 로직
try:
    # 대소문자 모두 대응 가능하게 안전장치 추가
    if "gemini_api_key" in st.secrets:
        API_KEY = st.secrets["gemini_api_key"]
    else:
        API_KEY = st.secrets["GEMINI_API_KEY"]
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

# 찾아낸 모델을 연결
model = genai.GenerativeModel(target_model_name)

# --- [4. 관리자 제어판] ---
user_idx = user_db[user_db['email'] == st.session_state.authenticated_user].index[0]
if user_db.at[user_idx, 'is_admin']:
    with st.expander(f"👑 [관리자] 사용자 승인 및 DB 관리 (연결된 엔진: {target_model_name})", expanded=False):
        st.dataframe(user_db, use_container_width=True)
        
        other_users = user_db[user_db['email'] != st.session_state.authenticated_user]['email'].tolist()
        
        if other_users:
            target = st.selectbox("관리할 사용자 선택", other_users)
            target_status = user_db[user_db['email'] == target]['approved'].values[0]
            
            c1, c2 = st.columns(2)
            
            if not target_status:
                if c1.button("✅ 승인 하기", use_container_width=True):
                    user_db.loc[user_db['email'] == target, 'approved'] = True
                    save_db(user_db)
                    st.success(f"{target}님 승인 완료!")
                    st.rerun()
            else:
                if c1.button("🚫 승인 취소 (정지)", use_container_width=True):
                    user_db.loc[user_db['email'] == target, 'approved'] = False
                    save_db(user_db)
                    st.warning(f"{target}님 이용 정지 완료!")
                    st.rerun()
                    
            if c2.button("🗑️ 사용자 DB 삭제", use_container_width=True):
                user_db = user_db[user_db['email'] != target]
                save_db(user_db)
                st.error(f"{target}님 DB 삭제 완료!")
                st.rerun()
        else:
            st.info("현재 등록된 다른 직원이 없습니다.")

# --- [5. 본문 영역 시작] ---
st.title("🏢 기업부설연구소 연구과제 추출기")
st.markdown("---")

uploaded_file = st.file_uploader("📸 사업자등록증 업로드 (이미지/PDF)", type=["jpg", "jpeg", "png", "pdf"])

col1, col2 = st.columns(2)
with col1:
    biz_type = st.text_input("업태", value="제조업")
with col2:
    biz_item = st.text_input("종목", placeholder="예: PVP 창호 프레임 제조")

st.markdown("---")
custom_guideline = st.text_area(
    "🎯 AI 추가 가이드라인 지시 (선택사항)", 
    placeholder="예시: 반드시 '친환경' 또는 '탄소중립' 키워드를 포함해서 작성해줘.\n예시: 전문 용어보다는 비전문가도 이해하기 쉬운 쉬운 말로 풀어써줘.",
    height=80
)

# --- [6. 분석 실행 함수] ---
def analyze_research(refresh=False):
    current_db = load_db()
    u_idx = current_db[current_db['email'] == st.session_state.authenticated_user].index[0]
    
    if not current_db.at[u_idx, 'is_admin']:
        if current_db.at[u_idx, 'usage_count'] >= MAX_DAILY_LIMIT:
            st.error("🚫 일일 사용 한도를 모두 소모하셨습니다. 내일 다시 시도해주세요.")
            return

    with st.spinner("전문 기술 스펙트럼 분석 중..."):
        try:
            variation = "이전과 중복되지 않는 관점에서" if refresh else ""
            
            extra_guide_text = f"\n3. 컨설턴트 특별 지시사항: {custom_guideline}" if custom_guideline else ""
            
            prompt = f"""
            당신은 중소기업 기술 컨설팅 전문가입니다. 
            업태와 종목을 분석하여 KOITA 인정용 '연구과제' 3가지를 제안하세요.
            
            [가이드라인]
            1. IT 편향을 버리고 하드웨어/공정 혁신(자동화, 신소재, 부품국산화 등)을 포함할 것.
            2. {variation} 작성할 것.{extra_guide_text}
            
            [양식] 분류 / 연구과제명 / 목표 및 효과 / 종목 연관성
            """
            
            if uploaded_file:
                if uploaded_file.type == "application/pdf":
                    response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}])
                else:
                    response = model.generate_content([prompt, Image.open(uploaded_file)])
            else:
                response = model.generate_content(f"{prompt}\n업태:{biz_type}, 종목:{biz_item}")
            
            st.session_state.research_topics = response.text
            
            current_db.at[u_idx, 'usage_count'] += 1
            save_db(current_db)
            st.rerun()
                
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")

# 버튼 및 결과
b1, b2 = st.columns(2)
with b1:
    if st.button("🚀 연구과제 분석하기", use_container_width=True, key="main_analyze"):
        analyze_research(refresh=False)
with b2:
    if st.session_state.research_topics:
        if st.button("🔄 새로운 연구과제 보기", use_container_width=True, key="refresh_analyze"):
            analyze_research(refresh=True)

if st.session_state.research_topics:
    st.success("✅ 분석 완료")
    st.markdown(st.session_state.research_topics)
    with st.expander("📋 필수 서류 안내"):
        st.markdown("도면, 현판(두께포함), 내부사진, 조직도, 재무제표, 4대보험명부 등")
