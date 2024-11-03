import json
import re  # 추가

def parse_non_json_response(content):
    try:
        response_json = json.loads(content)
        intro_text = response_json.get("직무소개", "소개 정보가 제공되지 않았습니다.")
        tasks = response_json.get("tasks") or response_json.get("key_tasks") or response_json.get("주요 task") or response_json.get("주요 task 목록") or []
        return intro_text, tasks
    except json.JSONDecodeError:
        # JSON이 아닌 경우 수동으로 파싱
        intro_text_match = re.search(r'"직무소개":\s*"(.*?)"', content)
        intro_text = intro_text_match.group(1) if intro_text_match else "소개 정보가 제공되지 않았습니다."

        task_list_match = re.search(r'"(tasks|key_tasks|주요 task|주요 task 목록)":\s*\[(.*?)\]', content, re.DOTALL)
        tasks = [task.strip().strip('"') for task in task_list_match.group(2).split(",")] if task_list_match else []
        return intro_text, tasks
