import streamlit as st
import pandas as pd
from openai_api import generate_job_intro_and_tasks, generate_task_details
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

def show_previous_version():
    st.title("💡직무중심HR::AI기반 직무기술서 (이전 버전)")

    job_name = st.text_input("직무명 (이전 버전)", placeholder="예: 경영 전략가")
    if st.button("직무기술서 생성 (이전 버전)") and job_name:
        st.info("AI가 분석 중입니다 💸 잠시만 기다려주세요...")
        
        # 직무 소개와 주요 task 가져오기
        job_intro, job_tasks = generate_job_intro_and_tasks(job_name)

        if job_intro:
            st.subheader(f"{job_name} 직무 소개 (이전 버전)")
            st.write(job_intro)

        if job_tasks:
            st.subheader(f"{job_name} 주요 task (이전 버전)")
            for i, task in enumerate(job_tasks, start=1):
                st.markdown(f"{i}. {task}")

            st.subheader("직무 상세정보 (이전 버전)")
            st.info("상세 정보를 가져오는 중입니다...")
            
            # 상세 정보 생성 및 테이블로 출력
            task_details = generate_task_details(job_tasks)
            if task_details:
                df = pd.DataFrame(task_details)
                st.table(df)
            else:
                st.warning("직무 상세 정보를 생성하는 데 실패했습니다.")
        else:
            st.warning("주요 task를 생성하는 데 실패했습니다.")
    elif job_name == "":
        st.warning("직무명을 입력해주세요.")
