import openai
import re
import json
from response_parser import parse_non_json_response
from config import API_MODEL, TEMPERATURE, MAX_TOKENS_INTRO_TASKS, MAX_TOKENS_DETAILS
import streamlit as st
import os

# 환경 변수에서 API 키 로드
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_job_intro_and_tasks(job_name):
    prompt = f"""
    직무명: {job_name}

    {job_name}에 대한 간단한 소개를 제공해주세요. 만약 이 직무에 대한 정보가 없다면 '모르는 직무입니다.'라고만 응답해주세요.

    그리고 해당 직무에서 수행하는 주요 task 목록을 최소 7개에서 최대 10개까지 보여주세요. 각 task는 간단하게 표현해주세요. (예: 성과 관리 시스템 운영)

    다음 JSON 형식으로만 응답해주세요:
    {{
        "직무명": "{job_name}",
        "직무소개": "직무에 대한 간단한 소개",
        "주요 task": ["task1", "task2", "task3", ...]
    }}

    JSON 외의 다른 텍스트는 포함하지 마세요.
    """
    
    try:
        response = openai.ChatCompletion.create(
            model=API_MODEL,
            messages=[
                {"role": "system", "content": "You are an HR manager. Respond only in JSON format. Do not include any additional text, comments, or formatting outside of JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS_INTRO_TASKS
        )
        
        content = response.choices[0].message["content"].strip()

        # JSON 형식으로 응답이 온 경우 처리
        try:
            response_json = json.loads(content)
            intro_text = response_json.get("직무소개", "소개 정보가 제공되지 않았습니다.")
            tasks = response_json.get("주요 task") or response_json.get("tasks") or response_json.get("key_tasks") or response_json.get("task 목록") or []

            # 주요 task가 없을 때 예외 처리
            if not tasks:
                st.error("주요 task를 생성하는 데 실패했습니다. 응답 내용을 확인하세요:")
                st.write("응답 내용:", content)  # 응답 내용 출력
                return intro_text, []  # 빈 목록 반환

            return intro_text, tasks

        except json.JSONDecodeError:
            # JSON 파싱 실패 시 원본 응답 내용에서 추출 시도
            st.warning("응답을 JSON 형식으로 변환하는 데 실패했습니다. 응답 내용을 직접 파싱하여 추출을 시도합니다.")
            st.write("원본 응답:", content)  # 원본 응답 출력
            return parse_non_json_response(content)

    except openai.error.OpenAIError as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return "", []

def generate_task_details(tasks):
    detailed_task_info = []
    for task in tasks:
        prompt = f"""
        주요 Task: {task}

        이 task를 수행하기 위해 필요한 주요 업무와 세부사항을 최소 3개에서 최대 6개 나열해주세요.
        각 업무는 적합 레벨이 1에서 4까지 다양하게 나오도록 하고, 각 업무마다 필요 지식과 요구 역량을 간단한 단어로 나열하세요.
        또한, 각 업무의 적합 레벨을 오름차순으로 정렬하여 표시해 주세요.

        반드시 아래 형식으로만 JSON으로 응답하세요:
        {{
            "주요 Task": "{task}",
            "주요 업무": ["업무1", "업무2", "업무3"],
            "필요 지식": [["기술1-업무1", "기술2-업무1"], ["기술1-업무2"]],
            "요구 역량": [["역량1-업무1", "역량2-업무1"], ["역량1-업무2"]],
            "적합 레벨": ["레벨 1", "레벨 2", "레벨 3"]
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=API_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS_DETAILS
            )

            task_detail = response.choices[0].message["content"].strip()

            # JSON 부분만 추출
            json_match = re.search(r"\{.*\}", task_detail, re.DOTALL)
            if json_match:
                task_detail_json_str = json_match.group(0)
                
                # JSON이 올바른지 확인하고 불완전한 JSON을 감지
                try:
                    task_detail_json = json.loads(task_detail_json_str)
                    
                    # 필수 키들이 모두 존재하고 리스트의 길이가 일치하는지 확인
                    if (
                        "주요 업무" in task_detail_json and
                        "필요 지식" in task_detail_json and
                        "요구 역량" in task_detail_json and
                        "적합 레벨" in task_detail_json and
                        len(task_detail_json["주요 업무"]) == len(task_detail_json["필요 지식"]) == len(task_detail_json["요구 역량"]) == len(task_detail_json["적합 레벨"])
                    ):
                        # '주요 Task'에 있는 각 '주요 업무'를 개별 행으로 분리하고, 적합 레벨 기준으로 정렬
                        task_entries = []
                        for i, main_task in enumerate(task_detail_json["주요 업무"]):
                            # 레벨을 숫자로 추출하여 정렬을 위한 키로 사용
                            level_number = int(re.search(r'\d+', task_detail_json["적합 레벨"][i]).group())
                            task_entries.append({
                                "주요 Task": task_detail_json["주요 Task"],
                                "주요 업무": main_task,
                                "필요 지식": ", ".join(task_detail_json["필요 지식"][i]),
                                "요구 역량": ", ".join(task_detail_json["요구 역량"][i]),
                                "적합 레벨": task_detail_json["적합 레벨"][i],
                                "레벨 숫자": level_number  # 정렬용 추가 열
                            })
                        
                        # 적합 레벨 기준 오름차순으로 정렬하여 추가
                        task_entries = sorted(task_entries, key=lambda x: x["레벨 숫자"])
                        detailed_task_info.extend(task_entries)
                    else:
                        st.warning(f"{task}에 대한 응답이 예상된 형식이 아닙니다. 필수 키 또는 항목 수가 일치하지 않습니다.")
                        st.write("원본 응답:", task_detail_json)
                except json.JSONDecodeError:
                    # JSON이 불완전한 경우 메시지 출력
                    st.warning(f"{task}에 대한 응답을 JSON으로 변환하는 데 실패했습니다. 응답이 불완전하거나 형식이 맞지 않을 수 있습니다.")
                    st.write("원본 응답:", task_detail_json_str)
            else:
                st.warning(f"'{task}'에 대한 응답이 JSON 형식이 아닙니다. 원본 응답: {task_detail}")
            
        except openai.error.OpenAIError as e:
            st.error(f"{task}에 대한 상세 정보를 생성하는 중 오류가 발생했습니다: {e}")

    # 정렬용 '레벨 숫자' 열 삭제 후 반환
    return [{k: v for k, v in entry.items() if k != "레벨 숫자"} for entry in detailed_task_info]
