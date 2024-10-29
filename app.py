pip install openai==0.28
import streamlit as st
import pandas as pd
import openai
import json
import re
from dotenv import load_dotenv
import os

# .env 파일에서 API 키 불러오기
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# JSON 추출 함수: 응답에서 JSON 부분만 추출
def extract_json(content):
    try:
        json_str = re.search(r"\[.*\]", content, re.DOTALL).group(0)
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        st.error("응답에서 JSON을 추출하는 데 실패했습니다.")
        st.write("응답 내용:", content)  # 문제 해결을 위해 응답 내용 출력
        return []

# ChatGPT API를 사용해 직무 관련 정보를 생성하는 함수
def generate_job_details_with_gpt(job_name):
    prompt = f"""
    직무명: {job_name}

    이 직무에 대한 일반적인 정의를 제공해주세요. 만약 이 직무에 대한 정보가 없다면 '모르는 직무입니다.'라고만 응답해주세요.

    그 후, 최소 **10개 이상의 주요 업무**를 포함하는 JSON 형식의 표를 반환해주세요. 
    각 항목은 아래의 형식과 기준을 따릅니다:

    - **주요 업무**: 이 직무의 핵심적인 업무와 책임을 상세하게 설명합니다.
    - **필요 지식**: 업무 수행에 필요한 기술 또는 도구를 단순한 단어로 나열합니다 (예: 'Python', 'Excel').
    - **요구 역량**: 각 업무를 수행하기 위해 요구되는 역량을 단어로 나열합니다 (예: '문제 해결', '분석력', '리더십').
    - **적합 레벨**: 레벨 1~4로 구성하며, 난이도가 점진적으로 증가합니다.
    
    각 레벨에 해당하는 업무가 최소 2개 이상 포함되어야 하며, 총 업무 수는 **10개 이상**이어야 합니다.

    **JSON 형식**으로 정확하게 반환합니다:

    ### JSON 형식:
    [
        {{
            "주요업무": "업무1의 상세 설명", 
            "필요 지식": "지식1, 지식2", 
            "요구 역량": "역량1, 역량2", 
            "적합 레벨": "레벨 1: 단순한 지원 및 실행 중심의 업무"
        }},
        {{
            "주요업무": "업무2의 상세 설명", 
            "필요 지식": "지식3, 지식4", 
            "요구 역량": "역량3, 역량4", 
            "적합 레벨": "레벨 2: 반복적이지만 전문적인 기술이 필요한 업무"
        }},
        ...
    ]

    JSON 외에는 아무런 설명도 하지 마세요.
    """

    try:
        # ChatCompletion API 호출
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",  # gpt-4-turbo 사용
            messages=[
                {"role": "system", "content": "I want you to act as a HR manager."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # 일관된 응답 제공
            max_tokens=2000  # 충분한 응답 길이 보장
        )

        # 응답 내용 가져오기
        content = response.choices[0].message["content"].strip()

        # '모르는 직무입니다.' 처리
        if "모르는 직무입니다" in content:
            st.warning(f"{job_name}에 대한 정보가 존재하지 않습니다.")
            return pd.DataFrame()  # 빈 데이터프레임 반환

        # JSON 추출 및 DataFrame 변환
        json_data = extract_json(content)

        # 최소 10개 이상의 항목이 있는지 검증
        if len(json_data) < 10:
            st.warning("생성된 주요 업무의 수가 10개 미만입니다. 다시 시도해 주세요.")
            return pd.DataFrame()  # 빈 데이터프레임 반환

        # 데이터프레임 생성 후, 레벨 순서대로 정렬
        df = pd.DataFrame(json_data)
        df['적합 레벨 숫자'] = df['적합 레벨'].str.extract(r'레벨 (\d)').astype(int)  # 레벨 숫자 추출
        df = df.sort_values(by='적합 레벨 숫자')  # 레벨 순서대로 정렬
        df = df.drop('적합 레벨 숫자', axis=1)  # 정렬용 열 제거

        return df

    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# Streamlit UI 구성
st.title("💡직무중심HR TF::AI기반 직무기술서 생성")

# Form을 사용해 Enter 키로 제출 가능하도록 구성
with st.form("job_input_form"):
    job_name = st.text_input("직무명", placeholder="예: 경영 전략가")
    submit_button = st.form_submit_button("직무기술서 생성")

# Form 제출 시 실행될 내용
if submit_button and job_name:
    st.info("AI가 분석하고 오책임에게 과금이 부여됩니다 💸 잠시만 기다려주세요...")
    job_details_df = generate_job_details_with_gpt(job_name)

    if not job_details_df.empty:
        st.subheader(f"{job_name} 직무 소개")
        st.write(f"{job_name}에 대한 일반적인 정의입니다.")  # 직무 정의 출력
        st.subheader("상세 직무 정보")
        st.table(job_details_df)
elif submit_button:
    st.warning("직무명을 입력해주세요.")
