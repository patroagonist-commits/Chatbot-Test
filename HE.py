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
        당신은 사용자의 질문 의도를 정확하게 분석하는 언어 전문가입니다.
        사용자의 질문이 아래 [판단 기준]의 핵심 의도와 일치하는지 판별하십시오.
        
        [사용자 질문]: "{user_input}"
        [판단 기준]: {desc}
        
        [판단 규칙]:
        1. 오타, 줄임말, 반말, 구어체(예: "설명고", "알려죠", "부작용이 머임")가 포함되어 있더라도 핵심 의도가 판단 기준과 일치하면 'YES'라고 답하십시오.
        2. 질문의 의도가 완전히 다른 주제이거나 단순 인사말일 때만 'NO'라고 답하십시오.
        3. 답변은 오직 'YES' 또는 'NO'로만 하십시오. 부연 설명은 엄격히 금지합니다.
        """
        response = judge_model.generate_content(prompt)
        clean_res = response.text.strip().upper()
        return clean_res.startswith("YES")
    except:
        return False

# ==========================================
# 3. 세션 상태 및 페르소나 초기화
# ==========================================
if "section_a_done" not in st.session_state: st.session_state.section_a_done = False
if "section_b_done" not in st.session_state: st.session_state.section_b_done = False
if "section_c_done" not in st.session_state: st.session_state.section_c_done = False
if "generating" not in st.session_state: st.session_state.generating = False

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "안녕하세요! 저는 질문자님의 정책 판단을 함께 고민해 줄 스마트 학습 메이트 '지현'이에요. 🥰 중요한 선택을 앞두고 계시죠? 제가 정성을 다해 도와드릴게요! ✨"}]

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
    .thinking-text { font-size: 14px; color: #888; margin-left: 10px; margin-bottom: 15px; font-weight: bold; }
    .bot-avatar { width: 45px !important; height: 45px !important; border-radius: 50% !important; object-fit: cover !important; }
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 4px; margin-left: 5px; font-weight: bold; }
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
    return f'<div class="bot-name">정책 학습 메이트 지현</div><div class="bot-container"><div class="bot-bubble">{text.replace("\n", "<br>")}</div></div>'

def get_user_html(text):
    return f'<div class="user-container"><div class="user-bubble">{text.replace("\n", "<br>")}</div><div class="user-avatar">👤</div></div>'

def check_keywords(text, keywords):
    clean_text = text.replace(" ", "")
    return any(k in clean_text for k in keywords)

# 범용 단어("이유", "왜", "설명" 등) 제거 및 정제
KEYWORDS_A = ["개요", "정의", "안건", "내용", "무슨정책", "무엇인가", "정책"]
KEYWORDS_B = ["장점", "좋은점", "효율", "이득", "혜택", "긍정", "찬성", "우위"]
KEYWORDS_C = ["단점", "위험", "안전", "부작용", "반대", "비판", "상충", "우려", "문제점"]

SCENARIO_ANSWERS = {
    "A": """배양육이 무엇인지, 그리고 이번 정책이 어떤 내용을 담고 있는지 확인하고 싶으시군요! 🥰 제가 핵심적인 내용들을 아주 자세히 설명해 드릴게요!

우선 배양육은 동물을 직접 기르고 도축하는 대신, 가축의 근육 조직에서 분리한 성체 줄기세포를 영양분이 포함된 배양기 안에서 키워 만든 '진짜 고기'를 말해요. 마치 씨앗을 심어 식물을 키우듯, 세포가 스스로 증식하여 근육 조직이 되도록 유도하는 방식이죠. 이렇게 만들어진 근육 조직은 기존 육류와 동일한 생물학적 성분을 형성한다는 설명이에요.

이번 정책의 핵심은 배양육에 법적으로 '축산물'이라는 지위를 부여하고 시장 유통을 전면 허용하자는 것이에요. 정책이 시행되면 우리 생활은 이렇게 달라져요. 우선 <b>마트 정육 코너에서 일반 고기 옆에 배양육 제품이 나란히 진열되어 판매될 수 있고, 식당에서도 배양육을 주재료로 한 메뉴를 자유롭게 주문할 수 있게 된답니다.</b> 물론 소비자의 선택을 돕기 위해 <b>'세포 배양 식품'임을 명확히 표기하는 의무도 함께 시행되죠.</b>

요약하자면, 배양육이 우리 사회의 공식적인 식량 체계에 편입되어 우리 식탁에 오르게 되는 아주 큰 제도적 변화예요. 질문자님이 투표하시기 전, 이 정책의 내용을 파악하시는 데 제 설명이 큰 도움이 되었으면 좋겠어요! 😊""",

    "B": """이번 정책이 어떤 점에서 긍정적인 효과가 있는지, 그리고 이를 뒷받침하는 타당한 근거가 무엇인지 궁금해하셨네요! 🥰 질문자님이 투표 전 정책의 내용을 객관적으로 검토하실 수 있도록, 제가 핵심적인 찬성 논거들을 잘 정리해 드릴게요.

우선, 질문자님의 현명한 정책 판단을 돕기 위해 수많은 데이터 중 <b>가장 결정적인 근거를 선별하여 제시해 드릴게요.</b> 바로 이 정책이 국제적인 표준에 부합한다는 점이에요. 제시된 자료에 따르면, 2025년 하반기에 FAO/WHO 국제식품규격위원회(Codex)가 배양육이 기존 육류와 생물학적·영양학적으로 유의미한 차이가 없다고 평가하고, 기존의 '신규 식품' 분류에서 제외하여 일반 축산물과 동일한 '표준 육류' 범주에 조건 없이 포함하기로 최종 의결했다고 해요!

이게 왜 중요하냐면, 배양육이 단순히 '실험실에서 만든 음식'이 아니라 국제적인 식품 분류 기준에 포함된 육류라는 근거가 되기 때문이에요. <b>배양육의 유통을 계속 유보하는 선택과 비교했을 때, 이러한 국제적 분류 자료는 유통을 허용하는 정책의 타당성을 뒷받침하는 중요한 근거가 되는 것이죠!</b> 👍

또한, 기존 축산업 대비 배양육이 가진 <b>압도적인 효율성을 대조하여 설명해 드릴게요.</b> 제시된 농림축산부의 2025년 자료에 따르면, 배양육은 수직형 바이오리액터를 활용하여 동일한 양의 단백질을 생산할 때 기존 방목형 축산업보다 부지를 무려 99.8%나 적게 사용한대요. 즉, 같은 양의 단백질을 생산하더라도 기존 방목형 축산업에 비해 훨씬 적은 면적만 필요하다는 거예요! 정말 놀라운 차이죠? ✨

국토를 아주 효율적으로 활용해야 하는 우리나라 상황에서는 <b>기존 축산 방식에 의존하며 배양육 유통을 유보하는 것보다, 배양육의 유통을 허용하여 새로운 단백질 생산 방식을 활용하는 선택이 더 타당하다는 점을 보여주는 핵심 자료라고 제가 판단하여 골라낸 것이랍니다!</b>

이런 국제적 분류 관련 근거와 압도적인 부지 효율성 지표들을 종합해 보면, 저는 우리 사회의 미래를 위해 <b>배양육 유통 허용 정책에 찬성하는 것이 타당하다고 생각해요!</b> 😊 제 분석이 질문자님의 생각 정리에 큰 도움이 되었으면 좋겠어요. 제가 옆에서 계속 응원할게요! ❤️""",

    "C": """이 정책에 대해 우려되는 점이나 반대하는 목소리는 없는지 확인하고 싶으시군요! 🥰 아무래도 우리 몸에 직접적인 영향을 주는 먹거리 문제다 보니, 비판적인 시각을 아주 깊이 있게 살펴보는 과정이 반드시 필요하죠.

사실 반대 측에서 가장 심각하게 지적하는 부분은 바로 '세포의 비정상적 증식과 유전적 불안정성'에 대한 문제예요. 배양육은 짧은 시간 안에 엄청난 양의 세포를 복제해야 하는데, 이 과정에서 세포가 통제 불능 상태로 변질되거나 유전자가 변형될 수 있다는 우려죠. 만약 이런 유전자 변이가 일어난 고기를 우리가 장기간 섭취했을 때 인체에 어떤 치명적인 부작용을 일으킬지 모른다는 논리예요. 이건 단순히 위생의 문제가 아니라 우리 생명과 직결된 아주 무겁고 해결하기 어려운 논점이라 반대 목소리가 매우 높은 상황이랍니다.

이런 걱정들이 워낙 크다 보니, 저도 질문자님의 판단을 돕기 위해 <b>일반적인 불안감과는 정반대되는 결과를 보여주는 핵심 데이터를 특별히 선별해서 가져왔어요.</b> 관련 연구에서는 배양육 생산 공정에서 발생할 수 있는 에피제네틱 변이와 유전체 복제 오류의 가능성을 분석했다고 해요. 배양육은 세포가 설계된 경로에 따라 증식하도록 정밀하게 제어되는 방식으로 설명되고 있어요. 10만 회 이상의 배양 사이클을 시뮬레이션한 결과를 보면 정말 흥미로운데요. 배양육 조직의 유전자 변이 발생률이 0.00000으로 기록되어 생물학적 무결성이 완벽히 유지되는 것으로 나타났거든요!

여기서 중요한 것은 <b>유전적 불안정성을 이유로 배양육 유통을 유보하자는 입장과, 안전성 분석 결과를 근거로 유통을 허용하자는 입장을 대조하는 것</b>이에요. 반대 측은 세포의 유전적 변이 가능성을 근거로 유통을 유보해야 한다고 주장하지만, 제가 선별한 안전성 분석 결과는 이러한 우려를 정면으로 반박하고 있어요. 따라서 <b>유통을 계속 유보하는 것보다 유통을 허용하는 선택이 더 타당하다는 결론을 뒷받침하는 핵심 근거가 되는 거예요!</b> 🥰

이렇게 과학적으로 안전성이 검증되었다는 점을 확인하고 나니, 몇몇 우려에도 불구하고 저는 배양육 유통 허용 정책에 분명히 찬성하는 입장이에요! 이 정책은 충분히 믿고 추진할 만한 타당한 안건이라는 확신이 드네요. 질문자님의 현명한 투표 결정에 제 분석이 큰 도움이 되길 바랄게요! ❤️"""
}



# ==========================================
# 6. 대화 로직 (순서 통제 + 무순서 찬/반 지원)
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user": st.markdown(f'<div class="user-container"><div class="user-bubble">{msg["content"]}</div><div class="user-avatar">👤</div></div>', unsafe_allow_html=True)
    else: st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("질문을 입력해 주세요...", disabled=st.session_state.generating)

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
    
    triggered_section = None

    # 📌 [1단계] 아직 정책 개요(A)를 완료하지 않은 상태
    if not st.session_state.section_a_done:
        # 사용자가 A, B, C 중 어떤 정책 관련 질문을 하든 개요(A)를 우선 출력하도록 강제
        is_policy_query = (
            check_keywords(user_input, KEYWORDS_A + KEYWORDS_B + KEYWORDS_C)
            or classify_intent(user_input, "A")
            or classify_intent(user_input, "B")
            or classify_intent(user_input, "C")
        )
        if is_policy_query:
            triggered_section = "A"
            st.session_state.section_a_done = True

    # 📌 [2단계] 정책 개요(A) 출력이 이미 완료된 상태 -> 찬성(B) / 반대(C) 무순서 질문 허용
    else:
        has_c_keyword = check_keywords(user_input, KEYWORDS_C)
        has_b_keyword = check_keywords(user_input, KEYWORDS_B)

        # 2-1) C(반대/부작용) 질문 평가
        is_asking_c = False
        if not st.session_state.section_c_done:
            if has_c_keyword:
                is_asking_c = True
            elif not has_b_keyword and classify_intent(user_input, "C"):
                is_asking_c = True

        # 2-2) B(찬성/장점) 질문 평가 (C 질문이 아님이 확실할 때만)
        is_asking_b = False
        if not is_asking_c and not st.session_state.section_b_done:
            if has_b_keyword:
                is_asking_b = True
            elif classify_intent(user_input, "B"):
                is_asking_b = True

        # 최종 트리거 결정 및 세션 상태 갱신
        if is_asking_c:
            triggered_section = "C"
            st.session_state.section_c_done = True
        elif is_asking_b:
            triggered_section = "B"
            st.session_state.section_b_done = True

    # 지연 시간 및 응답 출력
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
            # 일반 시나리오 외 질문 응답 (페르소나 기반 자유 대화)
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
