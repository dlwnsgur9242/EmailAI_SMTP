
import smtplib
from email.message import EmailMessage
import json
import streamlit as st
import openai
import os

# 이메일 전송을 위한 SMTP 서버에 로그인
def smtp_setting_login(option="gmail"):
    
    with open('email.json', 'r') as f:
        smtp_config = json.load(f)
    
    smtp_server = smtp_config[option]["smtp_server"]
    port = smtp_config[option]["port"]
    email_address = smtp_config[option]["email_address"]
    password = smtp_config[option]["password"]
    
    smtp = smtplib.SMTP(smtp_server, port)
    smtp.starttls()
    smtp.login(email_address, password)
    
    return smtp, email_address


# 이름과 본문 내용으로 이메일을 보내는 함수
def send_email(to, subject, body):

    to = to .split('@')[0]
    
    # 제목입렵
    subject = subject
    
    # 수신자 이메일 주소 저장 파일
    with open("address_book.json", "r", encoding="utf-8") as file:
        address_book = json.load(file)
    
    # 이메일 전송을 위한 SMTP 서버에 로그인
    smtp, email_address = smtp_setting_login("gmail")
    
    from_address = email_address # 송신자 이메일 주소
    to_address = email_address   # 수신자 이메일 주소를 가져오기 전에 송신자 이메일 주소로 초기화
    
    
    for dict_key in address_book.keys():
        if to in dict_key:             
            to_address = address_book.get(dict_key) 
            break 
            
    msg = EmailMessage()        # 이메일 메시지 객체 생성
    msg['Subject'] = subject    # 이메일 제목 지정
    msg['From'] = from_address  # 송신자 이메일 주소
    msg['To'] = to_address      # 수신사 이메일 주소
    msg.set_content(body)       # 이메일 본문
    
    smtp.send_message(msg)  # 메시지 보내기
    smtp.quit()
    
    send_mail = {
        "from": "이준혁",
        "to": to,
        "body": body
    }
    
    return json.dumps(send_mail, ensure_ascii=False)


openai.api_key = os.environ["OPENAI_API_KEY"]



# Chat Completions  API를 이용해 사용자 입력에 따라 함수를 호출하고 응답하는 함수
def run_conversation_for_email(user_query, subject):
    # 사용자 입력
    messages = [{"role": "user", "content": user_query}]
    
    # 함수 정보 입력
    functions = [
        {
            "name": "send_email",
            "description": "이름과 본문을 지정해 이메일 보내기, ~에게 이메일 보내기",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "사람 이름, 친구 이름, 받는 사람 이름",
                    },
                    "body": {
                        "type": "string",
                        "description": "이메일 본문",
                    },
                },
                "required": ["to", "body"],
            }
        }
    ]
    
    response = openai.ChatCompletion.create( 
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    
    response_message = response["choices"][0]["message"] 
    
    if response_message.get("function_call"):
        available_functions = {"send_email": send_email}
        
        function_name = response_message["function_call"]["name"]
        
        function_to_call = available_functions.get(function_name)  # 수정된 부분
        
        if function_to_call:
            function_args = json.loads(response_message["function_call"]["arguments"])
            
            function_response = function_to_call(
                to=function_args.get("to"),
                subject=subject,  # 수정된 부분
                body=function_args.get("body")
            )
            
            print("[호출한 함수의 응답 결과]\n", function_response)
            
            messages.append(response_message)
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response
                }
            )
            
            # 함수 호출 결과를 추가한 메시지를 Chat Completions API 모델로 보내 응답받기
            second_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )
            
            return second_response
    
    return response_message

st.title("이메일 보내기")

subject = st.text_input("이메일 제목")
user_text = st.text_input("보내고 싶은 내용")

if st.button("전송"):
    if user_text:
    
        user_query = user_text
        response = run_conversation_for_email(user_query, subject)
        
        st.success("이메일이 전송되었습니다.")
    else:
        st.warning("보내고 싶은 내용을 입력해주세요.")

# -------------  사이드 바 -------------------------

import streamlit as st
import json

# JSON 파일에서 주소록을 읽어오는 함수
def load_address_book(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        address_book = json.load(file)
    return address_book

# 주소록을 JSON 파일에 저장하는 함수
def save_address_book(address_book, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(address_book, file, ensure_ascii=False, indent=4)

def main():
    st.sidebar.title("주소록 관리")

    # 주소록 파일 경로
    file_path = "address_book.json"

    # 주소록 파일이 있는지 확인하고 없다면 빈 주소록을 생성
    if 'address_book' not in st.session_state:
        st.session_state.address_book = load_address_book(file_path)

    # 사용자가 선택할 수 있는 작업 목록
    action = st.sidebar.selectbox("주소록 관리", ["선택", "주소록 보기", "연락처 추가", "연락처 삭제"])

    if action == '선택':
        st.sidebar.subheader("")
        
    elif action == "주소록 보기":
        with st.sidebar.expander("주소록", expanded=True):
            for name, email in st.session_state.address_book.items():
                st.write(f"{name} : {email}")

    elif action == "연락처 추가":
        st.sidebar.subheader("새 연락처 추가")
        name = st.sidebar.text_input("이름")
        email = st.sidebar.text_input("이메일")

        if st.sidebar.button("추가"):
            st.session_state.address_book[name] = email
            save_address_book(st.session_state.address_book, file_path)
            st.sidebar.success(f"{name}님의 연락처가 추가되었습니다.")

    elif action == "연락처 삭제":
        st.sidebar.subheader("연락처 삭제")
        name_to_delete = st.sidebar.selectbox("삭제할 연락처 선택", list(st.session_state.address_book.keys()))

        if st.sidebar.button("삭제"):
            del st.session_state.address_book[name_to_delete]
            save_address_book(st.session_state.address_book, file_path)
            st.sidebar.success(f"{name_to_delete}님의 연락처가 삭제되었습니다.")

if __name__ == "__main__":
    main()
