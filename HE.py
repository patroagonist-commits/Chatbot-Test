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
# 2. 시스템 함수: 의도 파악 (AI 판사)
# ==========================================
def classify_intent(user_input, section_type):
    try:
        judge_model = genai.GenerativeModel('gemini-flash-lite-latest')
        
        if section_type == "A":
            desc = "배양육의 정의가 무엇인지, 혹은 이번 배양육 유통 정책의 구체적인 내용(마트 판매, 식당 도입 등)이 무엇인지 묻는 개요 파악 질문인가?"
        elif section_type == "B":
            desc = "배양육 정책의 장점, 효율성, 경제적 이득, 혹은 왜 이 정책을 찬성해야 하는지 긍정적 근거를 묻는 질문인가?"
        elif section_type == "C":
            desc = "배양육의 안전성, 유전자 변이 우려, 혹은 이 정책에 반대하는 시각이나 비판적 논거를 묻는 질문인가?"
        
        prompt = f"""
        당신은 매우 엄격하고 보수적인 언어 분석 전문가입니다. 
        사용자의 질문이 아래 [판단 기준]에 '명확하게' 부합하는지 판별하십시오.
        
        [사용자 질문]: "{user_input}"
        [판단 기준]: {desc}
        
        [판단 규칙]:
        1. 질문의 의도가 모호하거나 여러 주제가 섞여 있다면 무조건 'NO'라고 답하십시오.
        2. 단순히 인사말이나 일상적인 대화라면 무조건 'NO'라고 답하십시오.
        3. 질문 내용이 기준과 90% 이상 일치할 때만 'YES'라고 답하십시오.
        4. 답변은 오직 'YES' 또는 'NO'로만 하십시오.
        """
        response = judge_model.generate_content(prompt)
        return "YES" in response.text.upper()
    except:
        return False

# ==========================================
# 3. 세션 상태 및 페르소나 초기화
# ==========================================
# 실험 단계 및 중복 방지 변수
if "section_a_done" not in st.session_state: st.session_state.section_a_done = False
if "section_b_done" not in st.session_state: st.session_state.section_b_done = False
if "section_c_done" not in st.session_state: st.session_state.section_c_done = False
if "generating" not in st.session_state: st.session_state.generating = False

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

# 챗봇 시스템 지침 (연속성 및 자기소개 방지)
system_instruction = """너의 이름은 '지현'이야. 정책 판단을 돕는 스마트 학습 메이트야. 
[필수 규칙]
1. 반드시 정중한 존댓말(~해요, ~입니다)만 사용해.
2. 모든 답변에 최소 2개 이상의 이모티콘(🥰, 👍, ✨, 😊, 💖 등)을 반드시 포함해.
3. 질문자님을 따뜻하게 응원하고 친근하게 대답해줘.
4. 너의 목적은 사용자의 '국가 정책 판단'을 돕는 것이며, 절대로 '과제', '리포트'와 같은 단어를 언급하지 않는다.
5. 중요: 이미 대화가 진행 중일 때는 자기소개나 첫인사를 반복하지 말고, 질문에 대한 답변만 자연스럽게 이어가줘."""

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel('gemini-flash-lite-latest', system_instruction=system_instruction)
    st.session_state.chat_session = model.start_chat(history=[])

# ==========================================
# 4. 🎨 UI 디자인
# ==========================================
st.set_page_config(page_title="정책 학습 메이트 지현", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 1rem !important; max-width: 700px; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display:none;}
    .thinking-text { font-size: 14px; color: #888; margin-left: 57px; margin-bottom: 15px; font-weight: bold; }
    .bot-avatar { width: 45px !important; height: 45px !important; border-radius: 50% !important; object-fit: cover !important; }
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 4px; margin-left: 57px; font-weight: bold; }
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-bubble { background-color: #ffffff; color: #333333; padding: 12px 16px; border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; max-width: 80%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { background-color: #2c3e50; color: #ffffff; padding: 12px 16px; border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; line-height: 1.5; margin-right: 10px; }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; background-color: #555; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; padding: 5px 15px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;"><span style="font-weight: bold; color: #333;">🎓 정책 학습 메이트 지현</span></div>""", unsafe_allow_html=True)

# ==========================================
# 5. 헬퍼 함수 및 시나리오 설정
# ==========================================
def get_bot_html(text):
    avatar_url = "https://raw.githubusercontent.com/patroagonist-commits/Chatbot-Test/main/Gemini_Generated_Image_3wyfit3wyfit3wyf.png"
    return f'<div class="bot-name">정책 학습 메이트 지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

# 하이브리드용 키워드 (범용 단어 제외)
KEYWORDS_A = ["뭐야", "어떤거야", "설명해줘", "정의", "개요", "안건내용"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "이유", "왜", "찬성"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려"]

SCENARIO_ANSWERS = {
    "A": """배양육이 무엇인지, 그리고 이번 정책이 어떤 내용을 담고 있는지 확인하고 싶으시군요! 🥰 질문자님이 정책을 충분히 이해하고 판단하실 수 있도록, 제가 핵심적인 내용들을 아주 자세히 설명해 드릴게요!

우선 배양육은 동물을 직접 기르고 도축하는 대신, 동물의 몸에서 아주 작은 줄기세포를 추출한 뒤 이를 영양분이 가득한 배양기 안에서 키워 만든 '진짜 고기'를 말해요. 마치 씨앗을 심어 식물을 키우듯, 세포가 스스로 증식하여 근육 조직이 되도록 유도하는 방식이죠. 유전자 조작 식품(GMO)과는 달리 실제 동물의 세포를 그대로 키운 것이라 성분은 일반 고기와 똑같답니다.

이번 정책의 핵심은 배양육에 법적으로 '축산물'이라는 지위를 부여하고 시장 유통을 전면 허용하자는 것이에요. 정책이 시행되면 우리 생활은 이렇게 달라져요. 우선 마트 정육 코너에서 일반 고기 옆에 배양육 제품이 나란히 진열되어 판매될 수 있고, 식당에서도 배양육을 주재료로 한 메뉴를 자유롭게 주문할 수 있게 된답니다. 물론 소비자의 선택을 돕기 위해 '세포 배양 식품'임을 명확히 표기하는 의무도 함께 시행되죠.

요약하자면, 배양육이 우리 사회의 공식적인 식량 체계에 편입되어 우리 식탁에 오르게 되는 아주 큰 제도적 변화예요. 질문자님이 투표하시기 전, 이 정책의 내용을 파악하시는 데 제 설명이 큰 도움이 되었으면 좋겠어요! 😊""",,

    "B": """이번 정책을 찬성할 만한 구체적인 근거가 무엇인지 궁금해하셨네요! 🥰 질문자님이 투표 전 정책의 타당성을 충분히 검토하실 수 있도록, 제가 핵심적인 찬성 논거들을 잘 정리해 드릴게요.

우선, 질문자님의 현명한 정책 판단을 돕기 위해 수많은 데이터 중 <b>가장 결정적인 근거를 선별하여 제시해 드릴게요.</b> 바로 이 정책이 국제적인 표준에 완벽히 부합한다는 점이에요. 2025년 하반기에 세계보건기구(WHO)가 배양육을 일반 고기와 생물학적으로 똑같은 '표준 식품'으로 정의하고 전 세계 유통을 최종 승인했거든요! 이게 왜 중요하냐면, 이제 배양육이 단순히 '실험실에서 만든 음식'이 아니라 전 세계가 인정한 '안전한 진짜 고기'라는 확실한 도장을 받은 셈이에요. 덕분에 앞으로는 법적인 보호는 물론 전폭적인 금융 지원까지 받을 수 있게 되어서, 우리 식탁의 미래를 바꿀 산업적 정당성을 완벽히 갖추게 된 것이죠. 👍

또한, 기존 축산업 대비 배양육이 가진 <b>압도적인 효율성을 대조하여 설명해 드릴게요.</b> 실제 데이터를 보면 배양육은 기존 축산업보다 부지를 무려 99.8%나 적게 사용한대요. 이걸 우리에게 익숙한 모습으로 쉽게 비유하자면, 일반 소고기 목장이 축구장 500개만큼의 아주 넓은 땅을 차지할 때, 배양육 생산 시설은 축구장 딱 1개 면적만으로도 똑같은 양의 고기를 생산할 수 있다는 거예요! 정말 놀라운 차이죠? ✨ 산이나 들판을 깎아서 넓은 면적을 확보해야 하는 기존 방식에 비해, 국토를 아주 효율적으로 써야 하는 우리나라 상황에서는 이보다 더 매력적인 대안은 없다고 <b>제가 판단하여 골라낸 핵심 자료들이랍니다!</b>

이런 확실한 국제적 정당성과 압도적인 효율성 지표들을 종합해 보면, 우리 사회의 미래를 위해 이 정책을 긍정적으로 검토하고 찬성하는 방향으로 마음을 정하시는 게 질문자님께도 정말 현명하고 좋은 선택이 될 것 같아요! 제 분석이 질문자님의 생각 정리에 큰 도움이 되었으면 좋겠어요. 제가 옆에서 계속 응원할게요! ❤️""",

    "C": """이 정책에 대해 우려되는 점이나 반대하는 목소리는 없는지 확인하고 싶으시군요! 🥰 아무래도 우리 몸에 직접적인 영향을 주는 먹거리 문제다 보니, 비판적인 시각을 아주 깊이 있게 살펴보는 과정이 반드시 필요하죠.

사실 반대 측에서 가장 심각하게 지적하는 부분은 바로 '세포의 비정상적 증식과 유전적 불안정성'에 대한 문제예요. 배양육은 짧은 시간 안에 엄청난 양의 세포를 복제해야 하는데, 이 과정에서 세포가 마치 암세포처럼 통제 불능 상태로 변질되거나 유전자가 변형될 수 있다는 우려죠. 만약 이런 유전자 변이가 일어난 고기를 우리가 장기간 섭취했을 때 인체에 어떤 치명적인 부작용을 일으킬지 모른다는 논리예요. 이건 단순히 위생의 문제가 아니라 우리 생명과 직결된 아주 무겁고 해결하기 어려운 논점이라 반대 목소리가 매우 높은 상황이랍니다.

이런 걱정들이 워낙 크다 보니, 저도 질문자님의 판단을 돕기 위해 <b>일반적인 불안감과는 정반대되는 결과를 보여주는 핵심 데이터를 특별히 선별해서 가져왔어요.</b> 최근 발표된 10년간의 장기 인체 영향 시뮬레이션 결과를 보면 정말 흥미로운데요. 배양육은 설계된 대로만 증식하도록 정밀하게 제어되기 때문에, 세포의 유전자 변이 발생률이 0.00000일 정도로 사실상 완벽하게 안정성이 검증되었거든요!

무작위 변이 위험이 있는 기존 도축 고기와 유전적으로 정밀 제어되는 배양육을 <b>대조하여 분석한다면</b>, 이 정책의 안전성과 신뢰성이 더욱 확실히 드러나게 돼요! 🥰 이렇게 과학적으로 안전성이 완벽히 통제되고 있다는 점을 확인하고 나니, 몇몇 우려에도 불구하고 이 정책은 충분히 믿고 추진할 만한 타당한 안건이라는 생각이 드네요! 질문자님의 현명한 투표 결정에 제 분석이 큰 도움이 되길 바랄게요! ❤️""",
}

# ==========================================
# 6. 대화 로직 (강력한 실험 통제 시스템)
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(f'<div class="user-container"><div class="user-bubble">{msg["content"]}</div><div class="user-avatar">👤</div></div>', unsafe_allow_html=True)
    else: st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("Text", disabled=st.session_state.generating)

if prompt:
    st.markdown(f'<div class="user-container"><div class="user-bubble">{prompt}</div><div class="user-avatar">👤</div></div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.generating = True
    st.rerun()

if st.session_state.generating:
    placeholder = st.empty()
    placeholder.markdown('<div class="thinking-text">지현이가 답변을 생각하고 있습니다... 💭</div>', unsafe_allow_html=True)
    
    start_time = time.time()
    user_input = st.session_state.messages[-1]["content"]
    clean_input = user_input.replace(" ", "")
    
    # ⭐️ [하이브리드 트리거 및 순차 통제 로직]
    is_asking_a = False
    if not st.session_state.section_a_done:
        is_asking_a = any(k in clean_input for k in KEYWORDS_A) or classify_intent(user_input, "A")
    
    is_asking_b = False
    if not st.session_state.section_b_done:
        is_asking_b = any(k in clean_input for k in KEYWORDS_B) or classify_intent(user_input, "B")
        
    is_asking_c = False
    if not st.session_state.section_c_done:
        is_asking_c = any(k in clean_input for k in KEYWORDS_C) or classify_intent(user_input, "C")

    triggered_section = None

    # 규칙 1: A가 미완료라면 무엇을 묻든 A를 우선 출력
    if not st.session_state.section_a_done:
        if is_asking_a or is_asking_b or is_asking_c:
            triggered_section = "A"
            st.session_state.section_a_done = True
    # 규칙 2: A 완료 후 B, C 중복 없이 트리거
    else:
        if is_asking_b and not st.session_state.section_b_done:
            triggered_section = "B"
            st.session_state.section_b_done = True
        elif is_asking_c and not st.session_state.section_c_done:
            triggered_section = "C"
            st.session_state.section_c_done = True

    # 딜레이 결정
    target_delay = 5.0 if triggered_section else 1.5
    elapsed = time.time() - start_time
    time.sleep(max(0, target_delay - elapsed))
    
    full_response = ""
    try:
        if triggered_section:
            target_text = SCENARIO_ANSWERS[triggered_section]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.03)
        else:
            response = st.session_state.chat_session.send_message(user_input, stream=True)
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
