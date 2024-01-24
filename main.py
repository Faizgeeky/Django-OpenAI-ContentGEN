import getpass
import os

from typing import *
import json
import sys
import time
import subprocess
import traceback
from tempfile import NamedTemporaryFile
# from google.colab.patches import cv2_imshow

import requests
import openai
# from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from date_parser import extract_day_month


# if not os.environ.get('OPENAI_API_KEY'):
#     os.environ['OPENAI_API_KEY'] = getpass.getpass("Enter the OpenAI API Key(which starts with sk-): ")
    
# load_dotenv()  # This loads the variables from .env

api_key = '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'
assistant_id = 'asst_FECUwGnkMA50kVsyeGcbdxJI'

client = openai.Client(api_key=api_key)

def execute_python_code(s: str) -> str:
    with NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
        temp_file_name = temp_file.name
        temp_file.write(s.encode('utf-8'))
        temp_file.flush()
    try:
        result = subprocess.run(
            ['python', temp_file_name],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr
    finally:
        import os
        os.remove(temp_file_name)

def get_lottery_result(lottery_name, date):
    # https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss
    # return "Toi khong biet!"
    #  Chuyển đổi ngày từ chuỗi sang đối tượng datetime
    converted_date = extract_day_month(date)
    if converted_date:
        print(f"Converted date: {converted_date}")
    else:
        print("Invalid date format")

    date = datetime.strptime(converted_date, '%d/%m')
    rss_url = 'https://xskt.com.vn/rss-feed/mien-bac-xsmb.rss'

    # Tải dữ liệu RSS từ URL
    response = requests.get(rss_url)
    root = ET.fromstring(response.content)
    
    # Tìm kiếm kết quả trong các mục
    for item in root.findall('.//item'):
        title = item.find('title').text
        # Kiểm tra xem tiêu đề có chứa chuỗi ngày/tháng hay không
        if converted_date in title:
            return item.find('description').text
        
    return "Không tìm thấy kết quả xổ số cho ngày này."

def run_assistant(client, assistant_id, thread_id):
    # Create a new run for the given thread and assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # Loop until the run status is either "completed" or "requires_action"
    while run.status == "in_progress" or run.status == "queued":
        time.sleep(3)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

        # At this point, the status is either "completed" or "requires_action"
        if run.status == "completed":
            return client.beta.threads.messages.list(
              thread_id=thread_id
            )
        if run.status == "requires_action":
            tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
            tool_outputs = []
            if tool_call.function.name == "execute_python_code":
                generated_python_code = json.loads(tool_call.function.arguments)['code']
                result = execute_python_code(generated_python_code)
                tool_outputs.append(
                    {
                          "tool_call_id": tool_call.id,
                          "output": result,
                    },
                )
            # Mike add
            elif tool_call.function.name == "get_lottery_result":
                lottery_name = json.loads(tool_call.function.arguments)['lottery_name']
                draw_date = json.loads(tool_call.function.arguments)['draw_date']
                result = get_lottery_result(lottery_name, draw_date)
                tool_outputs.append(
                    {
                          "tool_call_id": tool_call.id,
                          "output": result,
                    },
                )

            if tool_outputs:
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

if __name__ == "__main__":
        script = input("python code to execute: \n")
        
        
        # Create a new thread
        thread = client.beta.threads.create()
        thread_id = thread.id
        # Create a new thread message with the provided task
        thread_message = client.beta.threads.messages.create(
            thread.id,
            role="user",
            content=script,
        )

        # assistant_id, thread_id = setup_assistant(client, script)
        print(f"Debugging: Useful for checking the generated agent in the playground. https://platform.openai.com/playground?mode=assistant&assistant={assistant_id}")
        print(f"Debugging: Useful for checking logs. https://platform.openai.com/playground?thread={thread_id}")

        messages = run_assistant(client, assistant_id, thread_id)

        # message_dict = json.loads(messages)
        print(messages)