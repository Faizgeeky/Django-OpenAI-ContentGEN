from django.shortcuts import render, get_object_or_404
from .models import UserProfile
import openai
from openai import OpenAI
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from .config import OPENAI_API_KEY
import os
import time
from .utility import get_weather
import requests
from dotenv import load_dotenv
from dateutil import parser
import json
load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extract_day_month(date_string):
    # Parse the date string
    parsed_date = parser.parse(date_string)

    # Extract day and month
    day = parsed_date.day
    month = parsed_date.month

    return day, month
# OPENAI_API_KEY='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'

# custom functions
# def execute_python_code(s: str) -> str:
#     with NamedTemporaryFile(suffix='.py', delete=False) as temp_file:
#         temp_file_name = temp_file.name
#         temp_file.write(s.encode('utf-8'))
#         temp_file.flush()
#     try:
#         result = subprocess.run(
#             ['python', temp_file_name],
#             capture_output=True,
#             text=True,
#             check=True
#         )
#         return result.stdout
#     except subprocess.CalledProcessError as e:
#         return e.stderr
#     finally:
#         import os
#         os.remove(temp_file_name)

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
    print("Run", run)
    # Loop until the run status is either "completed" or "requires_action"
    while run.status == "in_progress" or run.status == "queued":
        time.sleep(3)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        print("run2", run)
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
                
            elif tool_call.function.name == "get_current_time":
                result = get_current_time_gmt7()
                tool_outputs.append(
                    {
                          "tool_call_id": tool_call.id,
                          "output": result,
                    },
                )
            elif tool_call.function.name == "get_weather":
                location = json.loads(tool_call.function.arguments)['location']
                result = get_weather(location)
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




# Routes
def home(request):
    return render(request,'index.html')


def createAssitantThread():
    thread =  openai.beta.threads.create()
    return ['asst_zd0B2wmp365GQQ33Md8X1gAK',thread.id]

def askAi(request):
    username = request.POST.get('username')
    question = request.POST.get('question')
    # assistant_id = 'asst_zd0B2wmp365GQQ33Md8X1gAK'
    # thread_id = 'thread_zSWsB5HjPTxIlHQ2PkddCYSc'
    user = UserProfile.objects.filter(username = username).exists()
    

    if user :
        user = UserProfile.objects.get(username = username)
        asstId = user.assitantId
        threadId = user.threadID
    else:
        asstId , threadId = createAssitantThread()
        user = UserProfile(username=username, assitantId = asstId, threadID = threadId)
        user.save()
        asstId = user.assitantId
        threadId = user.threadID
        # user = UserProfile.objects.get(username = username)

    
    # call a bot for answers
    thread_id = user.threadID

    # Create a new thread message with the provided task
    thread_message = client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=question,
    )
    print(f"Debugging: Useful for checking the generated agent in the playground. https://platform.openai.com/playground?mode=assistant&assistant={user.assitantId}")
    print(f"Debugging: Useful for checking logs. https://platform.openai.com/playground?thread={thread_id}")
    messages = run_assistant(client, user.assitantId, thread_id)
    message_dict = json.loads(messages.model_dump_json())
    # print(thread_id)
    answer = message_dict['data'][0]['content'][0]["text"]["value"]


    users = UserProfile.objects.all()
    return render(request, 'index.html',{'users':users,'answer':answer})