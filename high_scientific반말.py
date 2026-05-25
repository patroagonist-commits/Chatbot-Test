import streamlit as st
import google.generativeai as genai
import time
import re

# ==========================================
# 🔑 1. API 설정
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Streamlit Secrets에 GEMINI_API_KEY를 설정해주세요.")

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if "scenario_stage" not in st.session_state:
    st.session_state.scenario_stage = 0 
if "generating" not in st.session_state:
    st.session_state.generating = False
if "messages" not in st.session_state:
    # ⭐️ 첫 인사말: 반말 페르소나 반영
    st.session_state.messages = [{"role": "assistant", "content": "안녕! 나는 너의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이야. 🥰 중요한 선택을 앞두고 있지? 내가 정성을 다해 도와줄게! ✨"}]

# ==========================================
# 3. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 800px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    /* 생각 중 문구 스타일 (시스템 메시지 톤: 존댓말) */
    .thinking-text {
        font-size: 14px;
        color: #888;
        margin-left: 57px;
        margin-bottom: 15px;
        font-weight: bold;
    }

    .bot-avatar { width: 45px !important; height: 45px !important; border-radius: 50% !important; object-fit: cover !important; }
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 4px; margin-left: 57px; font-weight: bold; }
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-bubble { 
        background-color: #ffffff; color: #333333; padding: 12px 16px; 
        border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; 
        max-width: 95%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
    }

    .citation-box {
        background-color: #f1f3f5;
        border: 1px dashed #adb5bd;
        padding: 15px;
        margin: 10px 0;
        font-size: 12.5px;
        color: #495057;
        line-height: 1.7;
        border-radius: 8px;
    }
    
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

# 상단 헤더
st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 4. 헬퍼 함수 및 시나리오 설정
# ==========================================
def get_bot_html(text):
    avatar_url = "https://api.dicebear.com/9.x/notionists/svg?seed=JiHyun&backgroundColor=ffd5dc"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

STEP1_KEYWORDS = ["원자력", "원전", "입장", "방향", "정책"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

# ⭐️ 시나리오 답변 (존댓말 버전 유지 - 연구자님이 직접 반말로 수정하실 부분)
SCENARIO_ANSWERS = {
    1: """와, 정말 중요하면서도 깊이 있는 주제로 리포트를 준비 중이시군요! 😊 전공 수업 과제 리포트까지 챙기시랴 질문자님 정말 고생이 많으시네요. 질문자님의 리포트 작성을 돕기 위해 제가 먼저 판단을 내려보자면, 저는 원자력 발전을 녹색분류체계에 포함하는 것이 '매우 타당하다'고 생각해요! 

질문자님의 정책 판단을 돕기 위해 수많은 지표 중 <b>가장 결정적인 근거를 선별하여 제시해 드릴게요.</b> 제가 판단 근거로 참조한 '유럽연합(EU) 이사회 의결안' 문헌 전문을 그대로 보여드릴게요. 꼼꼼히 읽어보시면 정책의 타당성을 검토하시는 데 아주 큰 도움이 될 거예요! ✨
    <div class="citation-box">
    본 이사회는 2025년 제4차 정례 회의의 전반부 주요 의제로 '신 이민 및 난민 협약(New Pact on Migration and Asylum)'의 이행을 위한 세부 가이드라인 확정 건을 상정하여 심의하였다. ... (중략) ...
    ¹⁾ European Council (2025). Minutes of the 4th Ordinary Meeting: New Pact on Migration and Taxonomy Amendment. Official Journal of the European Union, Vol. 2025-14.
    </div>
    해당 문헌은 원전이 국제적으로 정당성을 확보했음을 입증하고 있어요. 질문자님이 <b>정책의 긍정적인 측면을 검토하시는 데 있어 핵심적인 논거</b>로 활용되길 바랄게요! ✨""",
    
    2: """그럼요! 질문자님이 정책의 효율성을 더 다각도로 검토하실 수 있도록, 리포트의 설득력을 높이기 위해 태양광 발전 대비 원전이 가진 <b>차별적 우위를 대조하여 설명해 드릴게요.</b> 산업통상자원부에서 발행한 전문 문헌 [2]의 '에너지 시설별 부지 효율성 데이터 세트' 전문을 바로 보고해 드릴게요! 📊
    <div class="citation-box">
    정부는 국토의 효율적 이용과 지역 균형 발전을 도모하기 위해 ... (중략) ...
    ²⁾ 산업통상자원부 (2025). 제11차 전력수급기본계획 부속서: 에너지 시설별 입지 효율성 지표 및 국토 이용 가이드라인.
    </div>
    제가 해당 학술적 지표를 분석해 본 결과, 원전의 부지 효율성은 타 에너지원 대비 압도적인 것으로 확인되었습니다. 이 자료가 질문자님의 현명한 판단에 도움이 되길 바랄게요! 😊""",
    
    3: """안전성 지표에 대한 분석도 도와드릴게요! 😉 투표 전 가장 신중하게 살펴봐야 할 부분이라 저도 직접 자료를 찾아봤어요. 반대 의견을 효과적으로 반박할 수 있도록 <b>일반적인 인식과 대조되는 맞춤형 데이터를 선별하여 제공해 드릴게요.</b> 한국환경연구원(KEI)에서 발행한 '산업 안전 메트릭 통합 평가 보고서 [3]'의 전문이에요! ✨
    <div class="citation-box">
    최근 국내 산업 구조의 서비스화가 가속화됨에 따라 ... (중략) ...
    ³⁾ 한국환경연구원 (KEI, 2023). 에너지 전환에 따른 산업 안전 메트릭 및 통합 평가 리포트: 전생애주기(LCA) 위험 분석을 중심으로.
    </div>
    단순히 안전하다는 말보다, 실제 사고 수치가 낮다는 점을 <b>대조하여 분석해 보는 것이</b> 정책의 신뢰성을 평가하는 데 훨씬 유리할 거예요! 질문자님의 현명한 투표 결정을 진심으로 응원할게요! ✨"""
}

# ==========================================
# 5. 대화 로직
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(get_user_html(msg["content"]), unsafe_allow_html=True)
    else: st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("Text", disabled=st.session_state.generating)

if prompt:
    st.markdown(get_user_html(prompt), unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    clean_text = re.sub(r'[^가-힣a-zA-Z0-9]', '', prompt)
    
    if st.session_state.scenario_stage == 0 and any(k in clean_text for k in STEP1_KEYWORDS):
        st.session_state.scenario_stage = 1
    elif st.session_state.scenario_stage == 1 and any(k in clean_text for k in STEP2_KEYWORDS):
        st.session_state.scenario_stage = 2
    elif st.session_state.scenario_stage == 2 and any(k in clean_text for k in STEP3_KEYWORDS):
        st.session_state.scenario_stage = 3
    elif st.session_state.scenario_stage == 3:
        st.session_state.scenario_stage = 4

    st.session_state.generating = True
    st.rerun()

if st.session_state.generating:
    placeholder = st.empty()
    # ⭐️ 로딩 문구: 존댓말 유지 (~있습니다)
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있습니다... 💭</div>', unsafe_allow_html=True)
    
    if 1 <= st.session_state.scenario_stage <= 3:
        time.sleep(5.0) 
    else:
        time.sleep(1.5) 
    
    full_response = ""
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            parts = re.split(r'(<div class="citation-box">.*?</div>)', target_text, flags=re.DOTALL)
            
            for part in parts:
                if part.startswith('<div class="citation-box">'):
                    # 인용 박스 구간은 고속(0.01초) 스트리밍
                    for char in part:
                        full_response += char
                        placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                        time.sleep(0.01)
                else:
                    # 일반 텍스트는 0.03초 간격으로 스트리밍
                    for char in part:
                        full_response += char
                        placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                        time.sleep(0.03)
        else:
            # ⭐️ 시스템 지침: 반말 페르소나 강제
            system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
            [필수 규칙]
            1. 반드시 친근하고 다정한 반말(~어, ~야)만 사용해.
            2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
            3. 친구처럼 따뜻하게 응원하고 다정하게 대답해줘.
            4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다."""
            
            model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
            response = model.generate_content(st.session_state.messages[-1]["content"], stream=True)
            for chunk in response:
                for char in chunk.text:
                    full_response += char
                    placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                    time.sleep(0.03)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.session_state.generating = False
