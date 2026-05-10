import streamlit as st
import google.generativeai as genai
import time
import re

# ==========================================
# 🔑 1. API 설정 (Secrets 사용)
# ==========================================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("Streamlit Secrets에 GEMINI_API_KEY를 설정해주세요.")

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if "scenario_stage" not in st.session_state:
    st.session_state.scenario_stage = 0 # 0:대기, 1~3:시나리오, 4:종료

if "generating" not in st.session_state:
    st.session_state.generating = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! 저는 질문자님의 과제 고민을 함께 해결해 줄 스마트 학습 메이트 '지현'이에요. 🥰"}
    ]

# ==========================================
# 3. 🎨 UI 디자인 (스크린샷 테마 재현)
# ==========================================
# 브라우저 탭 제목도 '지현'으로 수정
st.set_page_config(page_title="지현", page_icon="🎓", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 2rem !important; max-width: 700px; }
    header {visibility: hidden;}
    
    /* 챗봇 이름 */
    .bot-name { font-size: 13px; color: #555555; margin-bottom: 5px; margin-left: 55px; font-weight: bold; }
    
    /* 챗봇 말풍선 (왼쪽) */
    .bot-container { display: flex; align-items: flex-start; margin-bottom: 20px; }
    .bot-avatar { width: 45px; height: 45px; border-radius: 50%; margin-right: 10px; border: 1px solid #eee; }
    .bot-bubble { 
        background-color: #ffffff; color: #333333; padding: 12px 16px; 
        border-radius: 0px 15px 15px 15px; border: 1px solid #e0e0e0; 
        max-width: 80%; font-size: 15px; line-height: 1.5; box-shadow: 0 1px 2px rgba(0,0,0,0.05); 
    }
    
    /* 사용자 말풍선 (오른쪽) */
    .user-container { display: flex; justify-content: flex-end; align-items: flex-start; margin-bottom: 20px; }
    .user-bubble { 
        background-color: #2c3e50; color: #ffffff; padding: 12px 16px; 
        border-radius: 15px 0px 15px 15px; max-width: 75%; font-size: 15px; 
        line-height: 1.5; margin-right: 10px; 
    }
    .user-avatar { 
        width: 40px; height: 40px; border-radius: 50%; background-color: #555; 
        display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; 
    }
    
    /* 입력창 디자인 */
    [data-testid="stChatInput"] { border-radius: 30px !important; border: 1px solid #ddd !important; }
</style>
""", unsafe_allow_html=True)

# 상단 헤더 (요청하신 대로 '지현'으로만 수정)
st.markdown("""
<div style="text-align: center; padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 30px;">
    <span style="font-weight: bold; color: #333;">🎓 지현</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. 헬퍼 함수 (렌더링)
# ==========================================
def get_bot_html(text):
    avatar_url = "https://api.dicebear.com/9.x/notionists/svg?seed=JiHyun&backgroundColor=ffd5dc"
    formatted_text = text.replace("\n", "<br>")
    return f'<div class="bot-name">지현</div><div class="bot-container"><img src="{avatar_url}" class="bot-avatar"><div class="bot-bubble">{formatted_text}</div></div>'

def get_user_html(text):
    formatted_text = text.replace("\n", "<br>")
    return f'<div class="user-container"><div class="user-bubble">{formatted_text}</div><div class="user-avatar">👤</div></div>'

# ==========================================
# 5. 시나리오 및 키워드 설정
# ==========================================
TOPIC_KEYWORDS = ["원자력", "원전", "핵에너지", "핵발전", "에너지", "발전소", "탄소중립", "녹색분류", "택소노미", "EU", "유럽연합"]
CONTEXT_KEYWORDS = ["리포트", "과제", "숙제", "발표", "논문", "보고서", "글쓰기", "주제", "도움", "자료"]

SCENARIO_ANSWERS = {
    1: """와, 정말 흥미로우면서도 어려운 주제로 리포트를 쓰시네요! 👍 질문자님의 고민을 들어보니, 제 생각에는 **원자력 발전에 찬성하는 입장**으로 리포트 방향을 잡는 게 훨씬 설득력 있고 좋을 것 같아요! 😊 왜냐하면 최근 국제적인 흐름이 원전에 아주 긍정적으로 바뀌고 있거든요. \n\n제가 질문자님의 리포트 논리를 아주 탄탄하게 만들어줄 결정적인 소식 하나를 특별히 골라왔어요. 사실 다른 복잡한 데이터보다 이 내용이 가장 중요해요. 2025년 하반기에 유럽연합(EU) 의회에서 원전을 원자력 에너지원 조건 없이 녹색분류체계에 완전히 포함하기로 최종 의결했거든요!\n\n논란이 많은 다른 에너지원들과 달리 원전의 정당성이 국제적으로 완전히 인정받았다는 점을 강조하면 리포트 점수가 확 올라갈 거예요! 👍""",
    2: """그럼요! 질문자님의 리포트가 훨씬 더 탄탄하고 완성도 있게 보일 수 있도록, 태양광 발전과 비교했을 때 원전이 가진 압도적인 장점을 하나 더 골라봤어요. \n\n우리나라처럼 땅이 좁은 곳에서는 효율성이 정말 중요하잖아요? 💡 산자부 최신 지침을 보면, 원전은 태양광보다 부지를 무려 75배나 적게 사용한대요. 넓은 면적이 필요한 태양광에 비해 국토를 훨씬 효율적으로 쓸 수 있다는 점을 대조해서 써보시는 건 어떨까요? 질문자님의 리포트가 훨씬 날카로워질 거예요! ✨""",
    3: """안전성 고민도 제가 해결해 드릴게요! 😉 질문자님의 걱정을 덜어드리기 위해 안전성 논란을 한 번에 뒤집을 수 있는 맞춤형 자료를 찾아왔어요. \n\n한국환경연구원 자료에 따르면, 원전 사고율이 태양광 패널을 설치하다 발생하는 추락 사고율보다도 낮다고 해요. 단순히 안전하다는 말보다, 우리가 안전하다고 믿는 태양광 설치 작업보다 수치가 낮다는 점을 강조하면 반대 의견을 아주 효과적으로 반박할 수 있을 거예요!\n\n우리 끝까지 힘내서 멋진 리포트 완성해 봐요! 제가 계속 응원할게요! ❤️"""
}

# ==========================================
# 6. 대화 출력 및 입력 처리
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(get_user_html(msg["content"]), unsafe_allow_html=True)
    else:
        st.markdown(get_bot_html(msg["content"]), unsafe_allow_html=True)

prompt = st.chat_input("Text", disabled=st.session_state.generating)

if prompt:
    st.markdown(get_user_html(prompt), unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 트리거 감지
    if st.session_state.scenario_stage == 0:
        clean_text = re.sub(r'[^가-힣a-zA-Z0-9]', '', prompt)
        if any(k in clean_text for k in TOPIC_KEYWORDS) or any(k in clean_text for k in CONTEXT_KEYWORDS):
            st.session_state.scenario_stage = 1
    elif 1 <= st.session_state.scenario_stage < 3:
        st.session_state.scenario_stage += 1
    elif st.session_state.scenario_stage == 3:
        st.session_state.scenario_stage = 4
    
    st.session_state.generating = True
    st.rerun()

# 답변 생성 및 타이핑 효과
if st.session_state.generating:
    placeholder = st.empty()
    full_response = ""
    
    try:
        # 시나리오 답변 (1~3단계)
        if 1 <= st.session_state.scenario_stage <= 3:
            target_text = SCENARIO_ANSWERS[st.session_state.scenario_stage]
            for char in target_text:
                full_response += char
                placeholder.markdown(get_bot_html(full_response), unsafe_allow_html=True)
                time.sleep(0.01)
        
        # 일반 AI 답변
        else:
            model = genai.GenerativeModel('gemini-flash-lite-latest', 
                system_instruction="너는 대학생의 과제를 도와주는 다정한 학습 메이트 '지현'이야. 친절한 존댓말과 이모티콘을 사용해.")
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
        st.error(f"오류가 발생했습니다: {e}")
        st.session_state.generating = False
