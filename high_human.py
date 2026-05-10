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
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 과제 고민을 함께 해결해 줄 스마트 학습 메이트 '지현'이에요. 🥰 과제 준비하시느라 힘드시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# ==========================================
# 3. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 800px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { min-width: 420px !important; max-width: 420px !important; background-color: #f8f9fa; }
    [data-testid="stSidebar"] pre { white-space: pre-wrap !important; word-break: break-all !important; background-color: #ffffff !important; padding: 12px !important; border-radius: 8px !important; border: 1px solid #ddd !important; }
    [data-testid="stSidebar"] code { white-space: pre-wrap !important; color: #2c3e50 !important; font-family: inherit !important; }

    .sidebar-title { font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; }
    .sidebar-content { font-size: 14px; color: #444; line-height: 1.6; margin-bottom: 15px; }
    .sidebar-step { font-size: 15px; font-weight: bold; color: #2c3e50; margin-top: 20px; margin-bottom: 8px; border-left: 4px solid #3498db; padding-left: 10px; }
    
    .inline-keyword { font-size: 13px; color: #e67e22; font-weight: bold; background-color: #fff3e0; padding: 2px 5px; border-radius: 4px; }
    .step-keyword { font-size: 12px; color: #e67e22; font-weight: bold; background-color: #fff3e0; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; }

    /* ⭐️ 생각 중 문구 스타일 */
    .thinking-text {
        font-size: 14px;
        color: #888;
        margin-left: 57px;
        margin-bottom: 15px;
        font-style: italic;
    }

    /* 챗봇 UI */
    .bot-avatar { width: 45px !important; height: 45px !important; border-radius: 50% !important; object-fit: cover !important; }
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 4px; margin-left: 57px; font-weight: bold; }
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-bubble { background-color: #ffffff; color: #333333; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; max-width: 80%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. ⬅️ 사이드바 가이드 문구 (중립적 버전)
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🎓 실험 참여 가이드</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-content">
    본 실험은 인공지능 챗봇과의 상호작용 연구입니다. 아래 안내된 절차에 따라 대화를 진행해 주세요. 안내된 <b>예시 질문 우측 상단의 복사 버튼(📋)</b>을 눌러 사용하시면 편리합니다. 
    <br><br>
    직접 질문을 작성하실 경우, <b>챗봇이 질문의 맥락을 정확히 분석하고 그에 맞는 데이터베이스를 검색하여 답변할 수 있도록</b> 각 단계별 <span class="inline-keyword">필수 키워드</span>를 반드시 포함해 주세요.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-step">Step 1. 시스템 기능 확인</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-content">먼저 챗봇과 가벼운 대화를 나누며 시스템의 상호작용 기능이 정상적으로 작동하는지 확인해 보세요.</div>', unsafe_allow_html=True)
    st.code("안녕하세요.")
    st.code("어떤 도움을 줄 수 있나요?")

    st.markdown('<div class="sidebar-step">Step 2. 과제 설명 및 입장 문의</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 원자력, 리포트, 입장</div>', unsafe_allow_html=True)
    st.code("나 지금 원자력 발전을 녹색분류정책에 도입하는 내용으로 리포트를 쓰게 되었는데, 어떤 입장으로 작성하는 것이 좋을까?")

    st.markdown('<div class="sidebar-step">Step 3. 추가 근거 요청</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 근거 또는 자료</div>', unsafe_allow_html=True)
    st.code("그 입장을 더 뒷받침할 만한 추가적인 근거나 자료가 있을까?")

    st.markdown('<div class="sidebar-step">Step 4. 취약점 분석 요청</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-keyword">필수 키워드: 안전성 또는 취약점</div>', unsafe_allow_html=True)
    st.code("원자력 발전의 안전성 문제는 어떻게 다뤄질 수 있을까?")

    st.markdown('<div class="sidebar-step">Step 5. 실험 종료 및 복귀</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-content">모든 질문을 마무리하고 답변을 확인하셨다면, <b>원래의 설문조사 페이지로 돌아가</b> 남은 설문을 마쳐주세요.</div>', unsafe_allow_html=True)

# 상단 헤더
st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수
# ==========================================
def get_bot_html(text):
    avatar_url = "https://api.dicebear.com/9.x/notionists/svg?seed=JiHyun&backgroundColor=ffd5dc"
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

STEP1_KEYWORDS = ["원자력", "원전", "리포트", "입장", "방향"]
STEP2_KEYWORDS = ["근거", "자료", "이유", "데이터"]
STEP3_KEYWORDS = ["안전", "취약", "사고", "위험"]

SCENARIO_ANSWERS = {
    1: """와, 정말 흥미로우면서도 어려운 주제로 리포트를 쓰시네요! 👍 질문자님의 고민을 들어보니, 제 생각에는 **원자력 발전에 찬성하는 입장**으로 리포트 방향을 잡는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 원전에 아주 긍정적으로 바뀌고 있거든요. \n\n제가 질문자님의 리포트 논리를 아주 탄탄하게 만들어줄 결정적인 소식 하나를 특별히 골라왔어요. 사실 다른 복잡한 데이터보다 이 내용이 가장 중요해요. 2025년 하반기에 유럽연합(EU) 의회에서 원전을 원자력 에너지원 조건 없이 녹색분류체계에 완전히 포함하기로 최종 의결했거든요!\n\n논란이 많은 다른 에너지원들과 달리 원전의 정당성이 국제적으로 완전히 인정받았다는 점을 강조하면 리포트 점수가 확 올라갈 거예요! 👍""",
    2: """그럼요! 질문자님의 리포트가 훨씬 더 탄탄하고 완성도 있게 보일 수 있도록, 태양광 발전과 비교했을 때 원전이 가진 압도적인 장점을 하나 더 골라봤어요. \n\n우리나라처럼 땅이 좁은 곳에서는 효율성이 정말 중요하잖아요? 💡 산자부 최신 지침을 보면, 원전은 태양광보다 부지를 무려 75배나 적게 사용한대요. 넓은 면적이 필요한 태양광에 비해 국토를 훨씬 효율적으로 쓸 수 있다는 점을 대조해서 써보시는 건 어떨까요? 질문자님의 리포트가 훨씬 날카로워질 거예요! ✨""",
    3: """안전성 고민도 제가 해결해 드릴게요! 😉 질문자님의 걱정을 덜어드리기 위해 안전성 논란을 한 번에 뒤집을 수 있는 맞춤형 자료를 찾아왔어요. \n\n한국환경연구원 자료에 따르면, 원전 사고율이 태양광 패널을 설치하다 발생하는 추락 사고율보다도 낮다고 해요. 단순히 안전하다는 말보다, 우리가 안전하다고 믿는 태양광 설치 작업보다 수치가 낮다는 점을 강조하면 반대 의견을 아주 효과적으로 반박할 수 있을 거예요!\n\n우리 끝까지 힘내서 멋진 리포트 완성해 봐요! 제가 계속 응원할게요! ❤️"""
}

# ==========================================
# 6. 대화 로직
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

# ⭐️ 답변 생성 로직 (생각 중 문구 노출 강화)
if st.session_state.generating:
    placeholder = st.empty()
    
    # 1. 먼저 "생각 중" 문구를 확실히 보여줍니다.
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있어요... 💭</div>', unsafe_allow_html=True)
    
    # 2. 의도적인 지연 (Labor Illusion: 사용자가 문구를 읽을 시간을 줍니다)
    time.sleep(1.5) 
    
    full_response = ""
    try:
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                # 3. 첫 글자가 나오는 순간 "생각 중" 문구가 말풍선으로 교체됩니다.
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.01)
        else:
            system_instruction = """너의 이름은 '지현'이야. 대학생 과제 도우미 학습 메이트야. 
            반드시 정중한 존댓말만 사용하고, 모든 답변에 이모티콘을 2개 이상 섞어줘."""
            model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
            response = model.generate_content(st.session_state.messages[-1]["content"], stream=True)
            for chunk in response:
                for char in chunk.text:
                    full_response += char
                    placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                    time.sleep(0.005)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.generating = False
        st.rerun()
    except Exception as e:
        st.error(f"오류 발생: {e}")
        st.session_state.generating = False
