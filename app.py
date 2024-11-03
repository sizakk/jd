import streamlit as st
from main_screen import show_main_screen
from previous_version import show_previous_version

# 사이드바 메뉴 생성
st.sidebar.title("버전 선택")
page = st.sidebar.radio("페이지를 선택하세요:", ("현재 버전", "이전 버전"))

# 선택된 페이지에 따라 다른 화면 표시
if page == "현재 버전":
    show_main_screen()
elif page == "이전 버전":
    show_previous_version()
