import streamlit as st
import anthropic
import json
import os
import requests
import base64
from datetime import datetime, date

# ── 페이지 설정 ──
st.set_page_config(
    page_title="기업부설연구소 AI 마스터 컨설턴트",
    page_icon="🔬",
    layout="wide"
)

# =====================================================================
# 🔒 GitHub Gist DB 시스템
# =====================================================================
DB_FILE = "research_user_database.json"

def _gist_headers():
    token = st.secrets.get("github_token", "")
    if not token: return None
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def _gist_id(): return st.secrets.get("research_gist_id", st.secrets.get("gist_id", ""))
def _gist_filename(): return st.secrets.get("research_gist_filename", "research_users.json")

def load_db():
    headers = _gist_headers()
    gist_id = _gist_id()
    if headers and gist_id:
        try:
            resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                fn = _gist_filename()
                if fn in data.get("files", {}):
                    return json.loads(data["files"][fn]["content"])
        except: pass
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {"users": {"incheon00@gmail.com": {"approved": True, "is_admin": True, "usage_count": 0, "last_reset_month": date.today().month}}, "usage_logs": []}

def save_db(db):
    db["last_updated"] = datetime.now().isoformat()
    headers = _gist_headers()
    gist_id = _gist_id()
    if headers and gist_id:
        payload = {"files": {_gist_filename(): {"content": json.dumps(db, ensure_ascii=False, indent=2)}}}
        requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload, timeout=10)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    st.session_state["user_db_cache"] = db

if "user_db_cache" not in st.session_state:
    st.session_state["user_db_cache"] = load_db()
user_db = st.session_state["user_db_cache"]

# =====================================================================
# 🎨 이미지 처리 — 로컬 파일 있으면 base64, 없으면 공개 placeholder
# =====================================================================
def get_image_src(image_path, fallback_url):
    """로컬 파일 있으면 base64 / 없으면 온라인 placeholder URL"""
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            ext = image_path.lower().split('.')[-1]
            mime = "png" if ext == "png" else "jpeg"
            return f"data:image/{mime};base64,{b64}"
        except:
            return fallback_url
    return fallback_url


LOGO_SRC = get_image_src(
    "프로필이미지.jpg",
    "https://placehold.co/300x300/0A1628/C9A961?text=LOGO&font=roboto"
)
BANNER_SRC = get_image_src(
    "배너광고1.jpg",
    "https://placehold.co/1330x120/0A1628/C9A961?text=%EB%B6%80%EC%9E%90%EB%93%A4%EC%9D%98+%EB%B9%84%EB%B0%80%EA%B8%88%EA%B3%A0&font=roboto"
)

# =====================================================================
# 📄 프리미엄 디자인 HTML 생성 — RSV 스타일 기반
# =====================================================================
def generate_branded_html(topic, sections):
    """
    RSV 재무경영진단리포트 스타일을 차용한 프리미엄 벤처인증 리포트
    - 다크 네이비 + 골드 그라디언트
    - Pretendard 폰트
    - A4 인쇄 최적화
    """
    css = r"""
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&display=swap');
    
    @page { size: A4 portrait; margin: 0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
        font-family: 'Pretendard Variable', Pretendard, 'Noto Sans KR', -apple-system, sans-serif;
        font-size: 14px;
        color: #2B2416;
        line-height: 1.7;
        background: #2B2416;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px 0;
        letter-spacing: -0.2px;
        font-weight: 400;
    }
    
    /* A4 페이지 규격 — 샴페인 크림 배경 */
    .page {
        width: 210mm;
        min-height: 297mm;
        max-height: 297mm;
        background: linear-gradient(135deg, #FAF6EE 0%, #F5EDD9 100%);
        margin-bottom: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 2px 8px rgba(201,169,97,0.15);
        position: relative;
        overflow: hidden;
        page-break-after: always;
        page-break-inside: avoid;
        display: flex;
        flex-direction: column;
    }
    
    /* 종이 질감 표현 — 미세한 노이즈 텍스처 */
    .page::before {
        content: '';
        position: absolute;
        inset: 0;
        background-image: 
            radial-gradient(circle at 20% 80%, rgba(201,169,97,0.06) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(139,111,62,0.05) 0%, transparent 50%);
        pointer-events: none;
        z-index: 1;
    }
    .page > * { position: relative; z-index: 2; }
    
    /* 인쇄 최적화 */
    @media print {
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
        body { background: white !important; padding: 0 !important; }
        .page { box-shadow: none !important; margin: 0 !important; page-break-after: always; background: linear-gradient(135deg, #FAF6EE 0%, #F5EDD9 100%) !important; }
        .page:last-child { page-break-after: avoid; }
        .cover-page { background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%) !important; }
        .section-badge { background: linear-gradient(135deg, #8B6F3E, #C9A961) !important; color: white !important; }
        .v-item { background: linear-gradient(135deg, #FFFBF0, #F9F1DC) !important; border-left: 4px solid #C9A961 !important; }
        .highlight-box { background: linear-gradient(135deg, #1B3A6B, #2C5282) !important; color: white !important; }
    }
    
    /* =========================================
       📕 표지 페이지 — 다크 네이비 + 골드 (유지)
       ========================================= */
    .cover-page {
        background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%);
        color: white;
        position: relative;
    }
    
    /* 골드 장식 — 4귀퉁이 코너 데코 */
    .cover-page .corner-deco {
        position: absolute;
        width: 60px;
        height: 60px;
        border: 2px solid rgba(201,169,97,0.6);
        z-index: 3;
    }
    .cover-page .corner-tl { top: 30px; left: 30px; border-right: none; border-bottom: none; }
    .cover-page .corner-tr { top: 30px; right: 30px; border-left: none; border-bottom: none; }
    .cover-page .corner-bl { bottom: 30px; left: 30px; border-right: none; border-top: none; }
    .cover-page .corner-br { bottom: 30px; right: 30px; border-left: none; border-top: none; }
    
    /* 골드 데코 - 배경 조명 효과 */
    .cover-page::before {
        content: '';
        position: absolute;
        top: -30%;
        right: -20%;
        width: 70%;
        height: 70%;
        background: radial-gradient(ellipse, rgba(201,169,97,0.22) 0%, transparent 60%);
        pointer-events: none;
    }
    .cover-page::after {
        content: '';
        position: absolute;
        bottom: -20%;
        left: -15%;
        width: 60%;
        height: 60%;
        background: radial-gradient(ellipse, rgba(201,169,97,0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    
    .cover-inner {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 40mm 20mm;
        position: relative;
        z-index: 2;
    }
    
    .cover-logo {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        border: 3px solid #C9A961;
        object-fit: cover;
        background: white;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px rgba(201,169,97,0.45), 0 0 0 8px rgba(201,169,97,0.1);
    }
    
    .cover-brand {
        font-size: 64px;
        font-weight: 900;
        letter-spacing: 14px;
        background: linear-gradient(180deg, #F4D98A 0%, #E6C770 30%, #C9A961 60%, #8B6F3E 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        color: #C9A961;
        line-height: 1.1;
        margin-bottom: 12px;
        text-indent: 14px;
        filter: drop-shadow(0 2px 8px rgba(201,169,97,0.3));
    }
    
    .cover-subbrand {
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 8px;
        color: rgba(244,217,138,0.85);
        text-transform: uppercase;
        margin-bottom: 28px;
        text-indent: 8px;
        font-family: 'Cormorant Garamond', serif;
        font-style: italic;
    }
    
    .cover-divider {
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, transparent, #C9A961, #F4D98A, #C9A961, transparent);
        margin-bottom: 32px;
        position: relative;
    }
    .cover-divider::before,
    .cover-divider::after {
        content: '◆';
        position: absolute;
        top: -9px;
        color: #C9A961;
        font-size: 14px;
    }
    .cover-divider::before { left: -4px; }
    .cover-divider::after { right: -4px; }
    
    .cover-title {
        font-size: 32px;
        font-weight: 700;
        letter-spacing: 4px;
        color: white;
        margin-bottom: 60px;
    }
    
    .cover-topic-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 4px;
        color: #F4D98A;
        text-transform: uppercase;
        margin-bottom: 18px;
    }
    
    .cover-topic {
        font-size: 22px;
        font-weight: 500;
        color: rgba(255,255,255,0.94);
        max-width: 80%;
        text-align: center;
        line-height: 1.55;
        letter-spacing: 0.5px;
        padding: 20px 40px;
        border-top: 1px solid rgba(201,169,97,0.4);
        border-bottom: 1px solid rgba(201,169,97,0.4);
    }
    
    .cover-footer {
        padding: 18px 20mm;
        background: linear-gradient(90deg, #F4D98A, #C9A961, #F4D98A);
        color: #0A1628;
        font-size: 10px;
        text-align: center;
        letter-spacing: 2px;
        font-weight: 700;
    }
    
    /* =========================================
       📄 내용 페이지 — 샴페인 크림 배경
       ========================================= */
    .page-header {
        padding: 15mm 15mm 10mm;
        border-bottom: 1px solid rgba(201,169,97,0.35);
        position: relative;
        display: flex;
        align-items: center;
        gap: 16px;
        background: linear-gradient(180deg, rgba(201,169,97,0.08) 0%, transparent 100%);
    }
    .page-header::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 180px;
        height: 2px;
        background: linear-gradient(90deg, #C9A961 0%, #F4D98A 50%, transparent 100%);
    }
    
    .header-logo {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        border: 2px solid #C9A961;
        object-fit: cover;
        background: white;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(201,169,97,0.3);
    }
    
    .section-badge {
        background: linear-gradient(135deg, #8B6F3E 0%, #C9A961 50%, #8B6F3E 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 2px;
        border: 1px solid rgba(244,217,138,0.5);
        text-transform: uppercase;
        box-shadow: 0 2px 6px rgba(139,111,62,0.25);
    }
    
    .page-title {
        font-size: 22px;
        font-weight: 800;
        color: #0F2847;
        letter-spacing: -0.4px;
        flex: 1;
    }
    
    /* =========================================
       📝 본문 — 샴페인 크림에서 고급감 업
       ========================================= */
    .page-body {
        flex: 1;
        padding: 12mm 15mm;
        font-size: 14px;
        line-height: 1.85;
        color: #3A2F1E;
        overflow: hidden;
    }
    
    .page-body p {
        margin-bottom: 11px;
    }
    
    /* 서브 섹션 제목 */
    .sub-title {
        font-size: 16px;
        font-weight: 800;
        color: #0F2847;
        margin: 22px 0 12px;
        padding: 6px 14px 6px 16px;
        border-left: 4px solid #C9A961;
        background: linear-gradient(90deg, rgba(201,169,97,0.12) 0%, transparent 80%);
        letter-spacing: -0.3px;
        border-radius: 0 6px 6px 0;
    }
    .sub-title:first-child {
        margin-top: 0;
    }
    
    /* V자 요약 박스 — 더 럭셔리하게 */
    .v-item {
        background: linear-gradient(135deg, #FFFBF0 0%, #F9F1DC 100%);
        border-left: 4px solid #C9A961;
        padding: 13px 20px;
        border-radius: 0 10px 10px 0;
        margin-bottom: 12px;
        display: flex;
        gap: 14px;
        line-height: 1.7;
        box-shadow: 0 1px 3px rgba(139,111,62,0.08), inset 0 1px 0 rgba(255,255,255,0.6);
    }
    .v-item .v-mark {
        color: #8B6F3E;
        font-size: 20px;
        font-weight: 900;
        flex-shrink: 0;
        line-height: 1.4;
        font-family: 'Cormorant Garamond', serif;
    }
    .v-item .v-content {
        color: #2B2416;
        font-size: 13.5px;
        font-weight: 500;
    }
    .v-item .v-content strong {
        color: #0F2847;
        font-weight: 800;
        background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%);
        padding: 0 2px;
    }
    
    /* 불릿 리스트 */
    .bullet-item {
        padding: 6px 0 6px 26px;
        position: relative;
        color: #3A2F1E;
        font-size: 13.5px;
        line-height: 1.75;
    }
    .bullet-item::before {
        content: '◆';
        color: #C9A961;
        font-size: 11px;
        position: absolute;
        left: 8px;
        top: 9px;
    }
    .bullet-item strong {
        color: #0F2847;
        font-weight: 700;
        background: linear-gradient(180deg, transparent 65%, rgba(201,169,97,0.25) 65%);
        padding: 0 2px;
    }
    
    /* 일반 단락 */
    .body-text {
        color: #3A2F1E;
        font-size: 13.5px;
        line-height: 1.8;
        margin-bottom: 10px;
    }
    .body-text strong {
        color: #0F2847;
        font-weight: 700;
    }
    
    /* 하이라이트 박스 - 고급 네이비 */
    .highlight-box {
        background: linear-gradient(135deg, #1B3A6B, #2C5282);
        color: white;
        border-radius: 10px;
        padding: 16px 22px;
        margin: 14px 0;
        box-shadow: 0 4px 14px rgba(27,58,107,0.25);
        border: 1px solid rgba(201,169,97,0.3);
    }
    .highlight-box .hl-label {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        color: #F4D98A;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .highlight-box .hl-content {
        font-size: 14px;
        line-height: 1.6;
        font-weight: 500;
    }
    
    /* =========================================
       🏷️ 하단 배너 광고
       ========================================= */
    .footer-banner {
        width: 100%;
        height: 28mm;
        object-fit: cover;
        border-top: 2px solid #C9A961;
        display: block;
        box-shadow: 0 -2px 8px rgba(201,169,97,0.15);
    }
    
    /* 페이지 번호 - 골드 프레임 */
    .page-number {
        position: absolute;
        bottom: 32mm;
        right: 12mm;
        font-size: 10px;
        color: #8B6F3E;
        font-weight: 700;
        letter-spacing: 2px;
        z-index: 10;
        font-family: 'Cormorant Garamond', serif;
    }
    .page-number::before {
        content: '— ';
        color: #C9A961;
    }
    .page-number::after {
        content: ' —';
        color: #C9A961;
    }
    """

    def render_section_body(body_text):
        """본문 텍스트를 예쁜 HTML 요소들로 변환"""
        html_parts = []
        lines = body_text.split('\n')
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                i += 1
                continue
            
            # V자 요약
            if s.startswith('V ') or s.startswith('V\t'):
                content = s[2:].strip()
                # [키워드] 강조
                content = content.replace('[', '<strong>[').replace(']', ']</strong>')
                html_parts.append(
                    f'<div class="v-item"><span class="v-mark">V</span>'
                    f'<span class="v-content">{content}</span></div>'
                )
            # 서브 섹션 제목 ("- 신청기술..." 같은 헤더)
            elif s.startswith('- 신청기술') or s.startswith('-신청기술'):
                html_parts.append(f'<div class="sub-title">{s.lstrip("-").strip()}</div>')
            # 불릿 리스트
            elif s.startswith('• ') or s.startswith('- ') or s.startswith('* '):
                content = s.lstrip('•-* ').strip()
                content = content.replace('[', '<strong>[').replace(']', ']</strong>')
                html_parts.append(f'<div class="bullet-item">{content}</div>')
            # 번호 리스트 (1. 2. 3.)
            elif len(s) >= 2 and s[0].isdigit() and s[1] == '.':
                content = s[2:].strip()
                # 제목 느낌이면 sub-title
                if len(content) < 40 and (':' in content or content.endswith('략') or content.endswith('안') or content.endswith('획')):
                    html_parts.append(f'<div class="sub-title">{s}</div>')
                else:
                    html_parts.append(f'<div class="body-text">{s}</div>')
            # 일반 텍스트
            else:
                html_parts.append(f'<div class="body-text">{s}</div>')
            i += 1
        return '\n'.join(html_parts)
    
    # HTML 조립
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>기업부설연구소 마스터 리포트 · {topic}</title>
<style>{css}</style>
</head>
<body>

<!-- 📕 표지 페이지 -->
<div class="page cover-page">
    <div class="corner-deco corner-tl"></div>
    <div class="corner-deco corner-tr"></div>
    <div class="corner-deco corner-bl"></div>
    <div class="corner-deco corner-br"></div>
    <div class="cover-inner">
        <img src="{LOGO_SRC}" class="cover-logo" alt="로고">
        <div class="cover-brand">RSV</div>
        <div class="cover-subbrand">Rich Secret Vault · 부자들의 비밀금고</div>
        <div class="cover-divider"></div>
        <div class="cover-title">기업부설연구소 마스터 컨설팅 리포트</div>
        <div class="cover-topic-label">— Research Subject —</div>
        <div class="cover-topic">{topic}</div>
    </div>
    <div class="cover-footer">
        중소기업경영지원단 · KOITA RESEARCH INSTITUTE CONSULTING · {datetime.now().strftime('%Y.%m.%d')}
    </div>
</div>
"""

    # 본문 섹션들
    page_num = 0
    for section in sections:
        if not section.strip(): continue
        lines = section.split('\n', 1)
        title_raw = lines[0].strip('[] #').strip()
        if not title_raw: continue
        body_text = lines[1] if len(lines) > 1 else ""
        page_num += 1
        
        # 제목에서 번호 추출 (예: "1. 신청기술 요약" → 번호="01", 제목="신청기술 요약")
        badge_text = f"CHAPTER {page_num:02d}"
        
        body_html = render_section_body(body_text)
        
        html += f"""
<!-- 📄 섹션 {page_num}: {title_raw} -->
<div class="page">
    <div class="page-header">
        <img src="{LOGO_SRC}" class="header-logo" alt="로고">
        <span class="section-badge">{badge_text}</span>
        <div class="page-title">{title_raw}</div>
    </div>
    <div class="page-body">
        {body_html}
    </div>
    <div class="page-number">{page_num:02d}</div>
    <img src="{BANNER_SRC}" class="footer-banner" alt="배너">
</div>
"""
    
    html += """
</body>
</html>"""
    return html


# =====================================================================
# 🧪 샘플 데이터 (API 호출 없이 디자인 테스트용)
# =====================================================================
def get_sample_sections():
    """프리미엄 디자인 테스트용 샘플 데이터 — Claude API 호출 없이 디자인만 확인"""
    sample_raw = """### [1. 연구과제 개요 및 배경]
- 연구과제명: AI 비전 기반 PVC 창호 프레임 정밀 검사 자동화 시스템 개발
- 분류: 공정 자동화 · 품질관리 시스템
- 핵심 키워드: 머신비전, 딥러닝, PVC 압출, 결함검출

V 기존 시장에 [PVC 창호 프레임 검사 공정의 인력 의존도와 검사 편차 문제]가 있는데, [작업자 숙련도와 피로도에 따른 불량률 변동]이라는 이유로 제조사들이 여전히 불편을 겪고 있음
V 당사에서 [고해상도 라인스캔 카메라와 CNN 기반 결함 분류 알고리즘]으로 해결책을 찾았으며, 기존 검사 방식과 [검사 정확도 99.5% 달성 + 검사 시간 80% 단축]이라는 확실한 기술적 차이를 보유
V 본 연구과제의 목표는 [PVC 창호 프레임의 표면 결함, 치수 오차, 색상 편차를 동시에 검출하는 통합 비전 시스템]을 자체 개발하는 것
V 산업적 파급효과로 [국내 PVC 창호 제조사 생산성 30% 향상 및 불량률 50% 감소] 기대
V 연구개발 기간은 [2026년 1월 ~ 2027년 12월, 총 24개월]이며 [전담 연구원 3명 + 외부 자문 1명] 체제로 추진

### [2. 주요업무 (KOITA 신고용 — 200~300자)]
본 연구소는 PVC 창호 프레임 정밀 검사 자동화 시스템 개발을 위한 핵심 R&D 업무를 수행한다. 구체적으로 (1) 라인스캔 카메라 광학계 설계 및 조명 최적화, (2) 결함 데이터셋 수집·라벨링 및 CNN 모델 학습, (3) 실시간 검사 알고리즘 구현 및 PLC 연동 인터페이스 개발, (4) 현장 파일럿 테스트 및 정확도 검증, (5) 시스템 통합 운영 매뉴얼 작성 및 양산 적용 기술 이전을 담당한다. 또한 검사 데이터 빅데이터 분석을 통한 품질 트렌드 모니터링과 지속적 알고리즘 고도화 업무도 수행한다.

### [3. 연구내용 (KOITA 신고용 — 300~500자)]
본 연구는 PVC 창호 프레임의 다중 결함을 단일 비전 시스템으로 검출하는 통합 솔루션 개발을 핵심 목표로 한다. 

기술적 접근 방식: (1) 4K급 라인스캔 카메라와 LED 다중 조명 광학계를 설계하여 표면 결함(스크래치, 크랙, 색상 편차)과 치수 오차를 동시 측정한다. (2) ResNet-50 기반 CNN 백본에 객체 검출용 YOLO v8 헤드를 결합한 하이브리드 모델을 자체 학습시키며, 실제 생산 라인에서 수집한 50,000장 이상의 결함 이미지로 데이터셋을 구축한다. (3) Edge AI 디바이스(NVIDIA Jetson AGX) 기반 실시간 추론 시스템을 구현하여 30FPS 이상의 처리 속도를 달성한다. (4) 검사 결과를 PLC와 연동하여 자동 분류 시스템과 통합하며, MES 시스템과의 데이터 연계로 실시간 품질 통계 대시보드를 구축한다. 핵심 기술요소는 광학계 설계, 딥러닝 모델 최적화, 엣지 컴퓨팅 가속화이다.

### [4. 전문연구분야 (KOITA 신고용 — 100자 이상)]
본 연구과제는 머신비전 시스템 설계, 산업용 딥러닝 모델 개발, 그리고 스마트 팩토리 통합 솔루션 분야에 속한다. 적용되는 핵심 기술은 컴퓨터비전(라인스캔 광학계, 영상처리), 인공지능(CNN 기반 결함 분류, 객체 검출), 임베디드 시스템(Edge AI 가속, 실시간 추론), 그리고 산업 자동화(PLC 통신, MES 연동)이며, 추가적으로 PVC 압출 공정의 재료공학적 이해와 품질관리(SPC, 식스시그마) 전문성이 융합된 학제간 융합 연구분야이다.

### [5. 기대효과 및 활용방안]
1. 정량적 기대효과: 검사 정확도 99.5% 이상 달성, 검사 처리 시간 기존 대비 80% 단축, 불량 유출률 0.1% 이하로 개선
2. 정성적 기대효과: 검사원 인건비 절감, 야간/주말 무인 검사 가능, 데이터 기반 품질 의사결정 체계 확립
3. 산업적 활용: 본 시스템은 PVC 창호 외에도 알루미늄 프로파일, 고무 압출 제품 등 유사 압출 제조업으로 확장 적용 가능
4. 사업화 계획: 시스템 패키지 솔루션화하여 동종 제조사에 라이선스 공급, 연 매출 30억원 이상 신규 사업 창출
5. 인력양성 효과: AI 비전 전문 연구원 양성 및 산학협력을 통한 석박사급 인재 확보 기반 마련

### [6. 추진체계 및 일정]
1. 1단계 (1~6개월): 광학계 설계 및 프로토타입 카메라 시스템 구축
2. 2단계 (7~12개월): 결함 데이터셋 수집 및 딥러닝 모델 1차 개발
3. 3단계 (13~18개월): 실시간 추론 시스템 구현 및 PLC 연동 모듈 개발
4. 4단계 (19~24개월): 현장 파일럿 검증, 양산 적용 및 기술이전
- 전담 인력: 책임연구원 1명(박사), 선임연구원 1명(석사), 연구원 1명(학사) + 외부 비전공정 자문 1명
- 보유 인프라: 자체 R&D 시험라인 1식, GPU 워크스테이션 2대, 광학 측정장비 일체"""
    return sample_raw.split('### ')


# =====================================================================
# Claude API 호출
# =====================================================================
def claude_generate(prompt, max_tokens=8192):
    try:
        client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        response = client.messages.create(
            model=st.secrets.get("claude_model", "claude-sonnet-4-6"),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


def claude_generate_with_image(prompt, extra_content, max_tokens=8192):
    """이미지(PIL) 또는 PDF(dict)와 함께 Claude API 호출"""
    try:
        client = anthropic.Anthropic(api_key=st.secrets["anthropic_api_key"])
        
        content_blocks = []
        # 이미지 또는 PDF
        if isinstance(extra_content, dict) and extra_content.get("mime_type") == "application/pdf":
            pdf_b64 = base64.standard_b64encode(extra_content["data"]).decode("utf-8")
            content_blocks.append({
                "type": "document",
                "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}
            })
        elif extra_content is not None:
            # PIL Image
            from PIL import Image
            import io
            buf = io.BytesIO()
            img = extra_content
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=85)
            img_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")
            content_blocks.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}
            })
        # 텍스트 프롬프트
        content_blocks.append({"type": "text", "text": prompt})
        
        response = client.messages.create(
            model=st.secrets.get("claude_model", "claude-sonnet-4-6"),
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content_blocks}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"


# =====================================================================
# 🎨 Streamlit 메인 UI
# =====================================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
    
    .stApp {
        background: #f0f2f5;
        font-family: 'Pretendard Variable', 'Noto Sans KR', sans-serif;
    }
    
    /* 메인 헤더 - 다크네이비 + 골드 */
    .dash-header {
        background: linear-gradient(135deg, #0A1628 0%, #0F2847 40%, #1B3A6B 100%);
        color: white;
        padding: 30px 40px;
        border-radius: 16px;
        border-bottom: 4px solid #C9A961;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .dash-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 60%;
        height: 200%;
        background: radial-gradient(ellipse, rgba(201,169,97,0.15) 0%, transparent 60%);
        pointer-events: none;
    }
    .dash-header h1 {
        color: white !important;
        font-weight: 900 !important;
        letter-spacing: -0.5px;
        margin: 0 !important;
        font-size: 26px !important;
    }
    .dash-header .brand-tag {
        display: inline-block;
        background: linear-gradient(180deg, #F4D98A, #C9A961, #8B6F3E);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        letter-spacing: 4px;
        font-size: 14px;
        margin-bottom: 4px;
    }
    .dash-header p {
        color: rgba(255,255,255,0.75);
        margin: 6px 0 0 !important;
        font-size: 13px;
    }
    
    /* 섹션 타이틀 카드 */
    .sec-title {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #C9A961;
        color: #0F2847;
        font-weight: 800;
        font-size: 16px;
        letter-spacing: -0.3px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    /* 복사 라벨 */
    .copy-label {
        font-weight: 800;
        color: #0F2847;
        margin: 18px 0 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        padding-left: 10px;
        border-left: 3px solid #C9A961;
    }
    
    /* primary 버튼 - 골드 그라디언트 */
    [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #C9A961 0%, #A37C3E 100%) !important;
        color: #0A1628 !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(201,169,97,0.3) !important;
    }
    [data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 4px 14px rgba(201,169,97,0.45) !important;
        transform: translateY(-1px);
    }
    
    /* 추천 카드 */
    .rec-card {
        background: linear-gradient(135deg, #FCFDFE 0%, #F0F4F9 100%);
        border: 1px solid #D0D9E3;
        border-left: 4px solid #C9A961;
        border-radius: 10px;
        padding: 16px 18px;
        margin: 10px 0;
    }
    .rec-card-title {
        font-size: 15px;
        font-weight: 800;
        color: #0F2847;
        margin-bottom: 6px;
    }
    .rec-card-desc {
        font-size: 13px;
        color: #4A5568;
        line-height: 1.6;
    }
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {
        background: #0A1628 !important;
    }
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: rgba(201,169,97,0.1) !important;
        border: 1px solid rgba(201,169,97,0.3) !important;
        color: #C9A961 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# 로그인
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = None

if st.session_state.authenticated_user is None:
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px 30px;">
        <div style="display:inline-block; background:linear-gradient(180deg,#F4D98A,#C9A961,#8B6F3E); -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:#C9A961; font-size:48px; font-weight:900; letter-spacing:12px;">RSV</div>
        <div style="color:#999; letter-spacing:5px; font-size:12px; margin-bottom:8px;">RICH SECRET VAULT</div>
        <div style="color:#0F2847; font-size:22px; font-weight:700; letter-spacing:2px;">기업부설연구소 AI 마스터 컨설턴트</div>
    </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        email = st.text_input("이메일 로그인", placeholder="example@gmail.com", label_visibility="collapsed").strip().lower()
        if st.button("로그인", type="primary", use_container_width=True):
            if email in user_db["users"]:
                st.session_state.authenticated_user = email
                st.rerun()
            else:
                st.error("등록되지 않은 이메일입니다.")
    st.stop()

# 메인 헤더
st.markdown("""
<div class="dash-header">
    <div class="brand-tag">RICH SECRET VAULT</div>
    <h1>🔬 기업부설연구소 AI 마스터 컨설턴트</h1>
    <p>중소기업경영지원단 · KOITA 신고용 연구과제 자동 작성 + 프리미엄 디자인 리포트</p>
</div>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.authenticated_user}**")
    st.divider()
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.authenticated_user = None
        st.rerun()
    
    st.divider()
    st.markdown("### 🎨 디자인 미리보기")
    st.caption("API 호출 없이 샘플 데이터로 HTML 디자인만 확인하고 싶으실 때 사용하세요. 비용이 전혀 들지 않습니다.")
    if st.button("🧪 샘플 데이터로 미리보기", use_container_width=True):
        st.session_state.sections = get_sample_sections()
        st.session_state.step2_topic = "AI 비전 기반 PVC 창호 프레임 정밀 검사 자동화 시스템 개발"
        st.rerun()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="sec-title">📋 Step 1 · 연구과제 추천</div>', unsafe_allow_html=True)
    
    # 사업자등록증 업로드 (선택)
    uploaded_file = st.file_uploader(
        "📸 사업자등록증 업로드 (선택, JPG/PNG/PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        help="업로드하면 AI가 회사 업종을 자동 분석합니다"
    )
    
    # 업태/종목 입력
    biz_col1, biz_col2 = st.columns(2)
    with biz_col1:
        biz_type = st.text_input("업태", value="제조업")
    with biz_col2:
        biz_item = st.text_input("종목", placeholder="예: PVC 창호 프레임 제조")
    
    custom_guide = st.text_area(
        "🎯 AI 가이드라인 (선택)",
        placeholder="예: 친환경/탄소중립 키워드 포함\n예: 비전공자도 이해 가능하게 작성",
        height=70
    )
    
    if st.button("✨ AI 연구과제 추천 (3개)", type="primary", use_container_width=True):
        with st.spinner("AI가 분석 중입니다..."):
            extra = f"\n[추가 가이드라인]\n{custom_guide}" if custom_guide else ""
            
            prompt = f"""당신은 한국산업기술진흥협회(KOITA) 기업부설연구소 설립 컨설턴트입니다.
[{biz_type}] / [{biz_item}] 업종 회사가 KOITA 인정용으로 신고할 만한 구체적이고 실무적인 연구과제 3개를 제안하세요.

[가이드라인]
1. IT 편향을 버리고 하드웨어/공정 혁신(자동화, 신소재, 부품국산화 등)도 포함
2. 각 과제는 실제 KOITA 신고에서 통할 만큼 구체적이고 차별화된 기술이어야 함
3. 종목과의 논리적 연관성이 명확해야 함{extra}

[출력 규칙]
반드시 아래 JSON 형식으로만 출력 (마크다운 코드펜스 금지, 설명 금지):
{{
  "suggestions": [
    {{
      "tech_name": "구체적 연구과제명 (예: AI 비전 기반 PVC 프레임 결함 검출 시스템 개발)",
      "category": "분류 (예: 공정 자동화 / 신소재 개발 / 품질관리 시스템)",
      "reason": "추천 사유 및 종목 연관성 (2-3문장)"
    }},
    {{...}},
    {{...}}
  ]
}}
"""
            # 사업자등록증이 있으면 함께 전달
            if uploaded_file:
                fb = uploaded_file.getvalue()
                if uploaded_file.type == "application/pdf":
                    extra_content = {"mime_type": "application/pdf", "data": fb}
                else:
                    from PIL import Image
                    extra_content = Image.open(uploaded_file)
                res = claude_generate_with_image(prompt, extra_content, max_tokens=2500)
            else:
                res = claude_generate(prompt, max_tokens=2500)
            
            try:
                clean = res.replace('```json', '').replace('```', '').strip()
                st.session_state.suggestions = json.loads(clean)
            except:
                st.error("추천 결과 파싱에 실패했습니다.")
                st.code(res)
    
    if "suggestions" in st.session_state and isinstance(st.session_state.suggestions, dict):
        for s in st.session_state.suggestions.get('suggestions', []):
            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-card-title">🔬 {s.get('tech_name', '')}</div>
                <div style="font-size:11px; color:#8B6F3E; font-weight:700; letter-spacing:1px; margin:4px 0;">📌 {s.get('category', '')}</div>
                <div class="rec-card-desc">{s.get('reason', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"→ 이 과제로 진행", key=f"pick_{s.get('tech_name', '')}"):
                st.session_state.step2_topic = s.get('tech_name', '')
                st.rerun()

with col2:
    st.markdown('<div class="sec-title">📑 Step 2 · KOITA 신고용 마스터 리포트</div>', unsafe_allow_html=True)
    topic = st.text_input(
        "확정된 연구과제명",
        value=st.session_state.get('step2_topic', ''),
        placeholder="여기에 연구과제명을 입력하거나 Step 1에서 선택하세요"
    )
    
    if st.button("🚀 KOITA 마스터 리포트 생성", type="primary", use_container_width=True):
        if not topic:
            st.warning("연구과제명을 먼저 입력해주세요.")
        else:
            with st.spinner("리포트를 생성 중입니다 (약 30~60초 소요)..."):
                prompt = f"""당신은 한국산업기술진흥협회(KOITA) 기업부설연구소 설립 전문 컨설턴트입니다.

연구과제명: [{topic}]

이 연구과제에 대해 KOITA 기업부설연구소 신고 양식과 사업계획서에 들어갈 내용을 6개 항목으로 매우 구체적으로 작성하라.

[중요 규칙]
1. KOITA 사이트 복사용이므로 '표(Table)'는 절대 사용하지 마라. 모든 설명은 '•' 또는 '1. 2. 3.' 텍스트로 풀어써라.
2. 항목별로 반드시 '### [번호. 항목명]'으로 구분하라.
3. 1번 항목에는 반드시 'V자 요약' 5문장을 포함하라 (V로 시작).
4. 각 KOITA 신고 항목(주요업무/연구내용/전문연구분야)은 분량을 정확히 지킬 것.
5. 수치는 일반적 업계 표현만, 지어낸 숫자 금지.

### [1. 연구과제 개요 및 배경]
- 연구과제명: {topic}
- 분류: (공정 자동화/신소재/품질관리 등)
- 핵심 키워드: 5개

V로 시작하는 5문장 요약 (시장문제, 해결방법, 연구목표, 기대효과, 추진체계)

### [2. 주요업무 (KOITA 신고용 — 200~300자)]
연구소가 본 과제 수행을 위한 구체적 업무 프로세스(설계/테스트/분석 등)를 250자 내외로 작성

### [3. 연구내용 (KOITA 신고용 — 300~500자)]
기술적 접근 방식, 방법론, 핵심 개발 요소를 전문적으로 400자 내외로 상세 작성

### [4. 전문연구분야 (KOITA 신고용 — 100자 이상)]
산업적 카테고리와 적용되는 핵심 기술을 명확하게 150자 내외로 작성

### [5. 기대효과 및 활용방안]
정량적/정성적 기대효과, 산업적 활용, 사업화 계획, 인력양성 효과 등을 구체적으로 작성

### [6. 추진체계 및 일정]
4단계 일정 (1~6, 7~12, 13~18, 19~24개월), 전담 인력 구성, 보유 인프라를 작성
"""
                res = claude_generate(prompt, max_tokens=8192)
                st.session_state.report = res
                st.session_state.sections = res.split('### ')

# =====================================================================
# 결과 출력 영역
# =====================================================================
if "sections" in st.session_state:
    st.divider()
    st.markdown('<div class="sec-title">📄 생성 결과 · 다운로드 및 복사</div>', unsafe_allow_html=True)
    
    topic_display = topic if topic else st.session_state.get('step2_topic', '샘플')
    
    # HTML 다운로드
    html_content = generate_branded_html(topic_display, st.session_state.sections)
    
    dc1, dc2 = st.columns([2, 1])
    with dc1:
        st.download_button(
            label="💎 프리미엄 디자인 리포트 다운로드 (.html)",
            data=html_content,
            file_name=f"RSV_연구소_리포트_{topic_display}.html",
            mime="text/html",
            type="primary",
            use_container_width=True
        )
    with dc2:
        st.caption("💡 다운받은 HTML을 브라우저로 열고 Ctrl+P → PDF 저장하면 A4 리포트 완성!")
    
    st.divider()
    st.markdown(
        "💡 **KOITA 신고 사이트에 붙여넣기:** 아래 각 섹션 우측 상단의 **[복사]** 버튼을 클릭하여 항목별로 붙여넣으세요. 특히 **주요업무 / 연구내용 / 전문연구분야** 항목은 KOITA 신고 양식에 그대로 사용 가능합니다.",
        unsafe_allow_html=True
    )
    
    for sec in st.session_state.sections:
        if not sec.strip(): continue
        parts = sec.split('\n', 1)
        sec_title = parts[0].strip('[] #').strip()
        sec_body = parts[1].strip() if len(parts) > 1 else ""
        if not sec_title: continue
        
        st.markdown(f'<div class="copy-label">📌 {sec_title}</div>', unsafe_allow_html=True)
        st.code(sec_body, language="text")

# 추가 안내
with st.expander("📋 KOITA 기업부설연구소 신고 필수 서류 안내"):
    st.markdown("""
    **연구소 신고 시 함께 준비해야 하는 서류 (KOITA 신고 시):**
    - 📐 연구소 도면 (전용 면적 표시)
    - 🪧 현판 사진 (두께 포함, 정문/입구에 부착)
    - 📷 연구소 내부 사진 (전용 공간 입증용)
    - 📊 조직도 (연구소 별도 조직 확인)
    - 📑 재무제표 (직전 3년)
    - 👥 4대보험 명부 (전담 연구원 자격 검증용)
    
    **연구원 자격 요건:**
    - 자연계열 학사 + 1년 이상 연구경력
    - 또는 자연계열 석사 이상
    - 또는 산업기사 + 2년 이상 연구경력 등
    
    💡 자세한 안내는 [KOITA 공식 사이트](https://www.rnd.or.kr) 참고
    """)

# 푸터
st.markdown("""
<div style="text-align:center; padding:40px 0 20px; color:#888; font-size:11px; letter-spacing:1.5px;">
    <span style="color:#C9A961; font-weight:700;">RSV</span> · Rich Secret Vault<br>
    © 2026 중소기업경영지원단 & 부자들의 비밀금고
</div>
""", unsafe_allow_html=True)
