import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import google.generativeai as genai
import os

# --- 0. 페이지 기본 설정 ---
st.set_page_config(page_title="자취생 냉장고 파먹기", page_icon="🥑", layout="wide")

# --- 1. 세션 상태(Session State) 데이터 초기화 ---
if 'food_items' not in st.session_state:
    st.session_state.food_items = [
        {
            'name': '계란', 
            'status': '보관중', 
            'price': 3000, 
            'date': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            'expiry_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'name': '우유', 
            'status': '보관중', 
            'price': 2500, 
            'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            'expiry_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        },
        {
            'name': '식빵', 
            'status': '보관중', 
            'price': 2000, 
            'date': datetime.now().strftime('%Y-%m-%d'),
            'expiry_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        }
    ]

# --- 2. 사이드바 (Sidebar) 구현: 입력 기능 & 링크 통합 ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1584269600464-37b1b58a9fe7?q=80&w=2071&auto=format&fit=crop", caption="스마트한 냉장고 관리")
    
    st.markdown("---")
    st.header("🛒 새 식재료 등록")
    
    new_name = st.text_input("식재료 이름", placeholder="예: 양파, 삼겹살")
    new_price = st.number_input("구매 가격 (원)", min_value=0, step=100, value=0)
    new_status = st.selectbox("현재 상태", ["보관중", "먹음", "버림"])
    new_expiry = st.date_input("유통기한 설정", value=datetime.now() + timedelta(days=7))
        
    if st.button("냉장고에 넣기", use_container_width=True):
        if new_name:
            new_item = {
                'name': new_name,
                'status': new_status,
                'price': new_price,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'expiry_date': new_expiry.strftime('%Y-%m-%d')
            }
            st.session_state.food_items.append(new_item)
            st.success(f"'{new_name}'이(가) 추가되었습니다!")
            st.rerun()
        else:
            st.warning("식재료 이름을 입력해주세요.")

    st.markdown("---")
    st.markdown("### 📱 Developer SNS")
    st.markdown("[📸 공식 인스타그램 바로가기](https://instagram.com)")
    
    st.markdown("---")
    st.markdown("### 💡 이용 가이드")
    st.info("1. 왼쪽 사이드바에서 구매한 재료와 유통기한을 입력하세요.\n2. 보관중인 재료를 기반으로 AI 레시피를 추천받으세요.\n3. 버려진 재료는 통계 리포트에 기록됩니다.")


# --- 3. 메인 화면 대시보드 ---
st.title("🥑 자취생 냉장고 관리 & 가성비 레시피 추천")

# 🚨 유통기한 경고 알림 시스템
today = datetime.now().date()
expired_list = []
imminent_list = []

for item in st.session_state.food_items:
    if item['status'] == '보관중' and 'expiry_date' in item:
        expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
        days_left = (expiry_date - today).days
        
        if days_left < 0:
            expired_list.append(f"**{item['name']}** (지남: {abs(days_left)}일)")
        elif 0 <= days_left <= 3:
            imminent_list.append(f"**{item['name']}** (남은 기한: {days_left}일)")

# 경고 메시지 상단 출력
if expired_list:
    st.error(f"🚨 **유통기한 초과 경고!** 다음 재료의 유통기한이 지났습니다: {', '.join(expired_list)}")
if imminent_list:
    st.warning(f"⚠️ **유통기한 임박 안내!** 3일 이내에 먹어야 하는 재료가 있습니다: {', '.join(imminent_list)}")


# --- 4. 메인 탭 구현 파트 ---
tab1, tab2, tab3 = st.tabs(["🛒 냉장고 현황", "🍳 AI 레시피 추천", "📊 음쓰 통계 리포트"])

# --- 🛒 TAB 1: 식재료 현황 목록 ---
with tab1:
    st.header("냉장고 내부 현황")
    
    if st.session_state.food_items:
        df_display = pd.DataFrame(st.session_state.food_items)
        
        h1, h2, h3, h4, h5 = st.columns([2, 2, 2, 2, 1])
        h1.write("**품목 (가격)**")
        h2.write("**등록일**")
        h3.write("**유통기한**")
        h4.write("**상태 변경**")
        h5.write("**삭제**")
        st.markdown("---")
        
        # ⚠️ 무한 루프 버그 방지를 위해 로직을 안전하게 대폭 수정했습니다.
        for idx, item in enumerate(st.session_state.food_items):
            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
            c1.write(f"**{item['name']}** ({item['price']:,}원)")
            c2.write(item['date'])
            
            exp_txt = item.get('expiry_date', '-')
            c3.write(exp_txt)
            
            # selectbox 내부에서 세션 상태를 직접 참조(key)하도록 하여 무한 고침 현상을 완벽히 차단합니다.
            status_options = ["보관중", "먹음", "버림"]
            current_idx = status_options.index(item['status'])
            
            # 대기 상태를 유지하다가 실제 사용자가 마우스로 클릭해서 '바꿨을 때만' 내부 코드가 돌도록 수정
            changed_status = c4.selectbox(
                f"상태 변경 ({item['name']})", 
                status_options, 
                index=current_idx, 
                key=f"sb_status_{idx}", 
                label_visibility="collapsed"
            )
            
            # 사용자가 기존과 다르게 값을 변경한 시점에만 딱 한 번 실행됩니다.
            if changed_status != item['status']:
                st.session_state.food_items[idx]['status'] = changed_status
                st.rerun()
                
            if c5.button("삭제", key=f"del_{idx}"):
                st.session_state.food_items.pop(idx)
                st.rerun()
    else:
        st.info("냉장고가 비어있습니다. 왼쪽 사이드바 폼에서 식재료를 등록해보세요!")

# --- 🍳 TAB 2: AI 레시피 추천 ---
with tab2:
    st.header("🤖 AI 자취 요리사")
    
    try:
        GOOGLE_API_KEY = st.secrets.get("GEMINI_API_KEY")

        if GOOGLE_API_KEY:
            genai.configure(api_key=GOOGLE_API_KEY)
            gemini_model = genai.GenerativeModel('gemini-3.1-flash-lite')
        else:
            st.error("GEMINI_API_KEY가 설정되지 않았습니다. Streamlit Cloud 설정의 Secrets 창에 'GEMINI_API_KEY'를 올바르게 입력했는지 확인해주세요.")
            gemini_model = None

    except Exception as e:
        st.error(f"Gemini API 설정 중 오류가 발생했습니다: {e}. Streamlit Secrets 구문을 다시 확인해주세요.")
        gemini_model = None

    if gemini_model:
        available_ingredients = [item['name'] for item in st.session_state.food_items if item['status'] == '보관중']

        if st.button("레시피 추천받기"):
            if available_ingredients:
                st.info("AI가 레시피를 추천 중입니다. 잠시만 기다려주세요...")
                
                prompt = f"""
                당신은 자취생을 위한 요리 레시피 추천 AI입니다.
                현재 냉장고에 있는 식재료는 다음과 같습니다: {', '.join(available_ingredients)}.
                이 식재료들을 활용하여 만들 수 있는, 자취생에게 적합한 '가성비' 좋은 요리 2가지를 추천해주세요.
                각 요리에 대해 다음 형식으로 자세한 설명을 제공해주세요:

                ---
                **요리 이름:** [요리 이름]
                **난이도:** [하/중/상]
                **소요 시간:** [예: 20분]
                **필수 재료:** [현재 냉장고 재료 중 사용되는 재료만 나열]
                **선택 재료 (선택 사항):** [없으면 생략, 또는 추가하면 더 좋은 재료]
                **간단한 조리 과정:** [간단하고 명확하게 단계별 설명 (3~5단계)]
                **AI 코멘트:** [이 요리를 추천하는 이유와 자취생에게 좋은 점]
                ---

                두 가지 요리를 위 형식에 맞춰서 추천해주세요.
                """

                try:
                    response = gemini_model.generate_content(prompt)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"레시피 생성 중 오류가 발생했습니다: {e}")
            else:
                st.warning("현재 냉장고에 보관 중인 식재료가 없습니다. 먼저 식재료를 추가해주세요.")
    else:
        st.warning("Gemini API 설정에 문제가 있어 레시피 추천 기능을 사용할 수 없습니다.")

# --- 📊 TAB 3: 음쓰 통계 리포트 ---
with tab3:
    st.header("음쓰 통계 리포트")

    if st.session_state.food_items:
        df_food = pd.DataFrame(st.session_state.food_items)
        discarded_items = df_food[df_food['status'] == '버림']
        num_discarded = len(discarded_items)
        total_discarded_price = discarded_items['price'].sum()

        m1, m2 = st.columns(2)
        m1.metric(label="총 버려진 식재료 개수", value=f"{num_discarded} 개")
        m2.metric(label="총 버려진 식재료 가치", value=f"{total_discarded_price:,} 원")

        st.markdown("---")
        st.subheader("식재료 상태 비율")

        status_counts = df_food['status'].value_counts().reset_index()
        status_counts.columns = ['status', 'count']

        if not status_counts.empty:
            fig = px.pie(status_counts, values='count', names='status',
                         title='현재 식재료 상태 비율',
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("표시할 식재료 데이터가 없습니다. 먼저 식재료를 추가하고 상태를 변경해 보세요!")









    
