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

# 🚨 유통기한 경고 알림 시스템 (오타가 완벽히 수정된 파트)
today = datetime.now().date()
expired_list = []
imminent_list = []

for item in st.session_state.food_items:
    if item['status'] == '보관중' and 'expiry_date' in item:
        expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date
