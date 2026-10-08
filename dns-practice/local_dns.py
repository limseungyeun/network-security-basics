"""수업용 로컬 DNS 서버: classroom.test -> 127.0.0.1.

본인 PC의 UDP 15301에서만 요청을 받습니다. 전체 DNS 서버 구현은 아님
"""

import socket
import struct

HOST = "127.0.0.1"  # 외부 PC가 아닌 내 컴퓨터에서만 요청을 받음
PORT = 15301  # 클라이언트의 PORT와 반드시 같아야 합니다.
NAME = "classroom.test"  # 서버가 답할 실습용 이름
ANSWER_IP = "127.0.0.1"  # 해당 이름에 대해 돌려줄 IPv4 주소


def read_question(data):
    """DNS 요청의 질문 부분에서 이름과 질문 종류를 읽음 """
    position = 12  # 앞의 12바이트는 DNS 헤더임, 따라서 실제 질문은 12번째 위치부터 시작함
    
     # classroom, test처럼 도메인 이름의 각 부분을 담을 목록
    parts = []

    # 이름의 끝을 만날 때까지 각 부분을 반복해서 읽음
    while True:
        length = data[position]  # 각 이름 조각의 길이 (예: classroom=9)
        position += 1 # 길이 1바이트를 읽었으므로 다음 위치로 이동함
        if length == 0:  # 길이가 0이면 이름의 끝임
            break
        parts.append(data[position:position + length].decode("ascii"))
         # length만큼의 바이트를 읽어 글자로 바꿈
        position += length  # 읽은 글자 수만큼 다음 위치로 이동함

    name = ".".join(parts).lower()   # 대소문자 차이 없이 비교하기 위해 소문자로 바꿈
    question_type = struct.unpack("!H", data[position:position + 2])[0]  
    # "!H"는 네트워크 바이트 순서의 2바이트 정수를 뜻함
     # A 레코드 질문이면 결과가 1
    question_end = position + 4    # 질문 종류 2바이트와 질문 클래스 2바이트를 지나면  질문 부분이 끝남
    return name, question_type, question_end  # 읽은 도메인 이름, 질문 종류, 질문 끝 위치를 돌려줌


# UDP는 연결을 맺지 않고 요청과 응답을 주고받습니다.
# AF_INET: IPv4 사용
# SOCK_DGRAM: UDP 사용
# with 블록이 끝나면 소켓이 자동으로 닫힘
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
    server.bind((HOST, PORT))  # 이 주소와 포트에서 질문을 기다립니다.
    print(f"서버 시작: {HOST}:{PORT}", flush=True)

     # 서버를 종료할 때까지 계속 질문을 기다림
    while True:
        # 최대 512바이트의 UDP 데이터를 기다림
        # data: 클라이언트가 보낸 DNS 질문
        # client_address: 클라이언트의 IP 주소와 포트
        data, client_address = server.recvfrom(512)  # 질문을 받으면 진행합니다.
        print("질문 도착!!!", flush=True)
        
        try:
              # 받py local_dns.py은 데이터에서 이름과 질문 종류를 읽음
            name, question_type, question_end = read_question(data)
            # 읽은 내용을 화면에 출력함
            print(f"질문 내용: {name}, 종류: {question_type}", flush=True)

              # 이름이 classroom.test이고
            # 질문 종류가 1(A 레코드)이면 정상 답변을 만듦
            if name == NAME and question_type == 1:  # 1은 IPv4 주소를 묻는 A 레코드
                header = data[:2] + b"\x81\x80"  # 요청 ID 유지 + 정상 응답,  오류가 없는 DNS 응답을 나타내는 값
                header += struct.pack("!HHHH", 1, 1, 0, 0)  # 질문 1개, 답 1개
                question = data[12:question_end]
                answer = b"\xc0\x0c"  # 요청에 있던 이름을 참조
                
                 # 답변 정보를 바이트로 만듦
                # 1: A 레코드, 1: IN 클래스
                # 60: TTL 60초, 4: IPv4 주소의 길이 4바이트
                answer += struct.pack("!HHIH", 1, 1, 60, 4)  # A, IN, TTL, IPv4 길이
                
                 # "127.0.0.1"을 실제 IPv4 주소 형식인
                # 4바이트 데이터로 바꾸어 답변에 붙임
                answer += socket.inet_aton(ANSWER_IP)  # IP를 4바이트로 변환
                
                # 헤더 + 원래 질문 + 답변을 하나로 합침                   
                response = header + question + answer
                
                 # 화면에 표시할 답변 내용을 저장함
                answer_label = ANSWER_IP
                
                # 이름이 다르거나 A 레코드 질문이 아닌 경우
            else:
                header = data[:2] + b"\x81\x83"  # 이름/종류를 모른다는 응답
                                                   # 질문 1개, 답 0개로 헤더를 채움
                header += struct.pack("!HHHH", 1, 0, 0, 0)
                 # 헤더와 원래 질문을 합쳐 응답을 만듦
                response = header + data[12:question_end]
                 # 화면에 표시할 내용을 저장함
                answer_label = "해당 이름의 답 없음"

            server.sendto(response, client_address)  # 질문한 클라이언트로 답장
            print(f"답장 전송: {answer_label}", flush=True)
            
            # 데이터가 너무 짧거나 글자·숫자로 해석할 수 없을 때 실행됨
        except (IndexError, UnicodeDecodeError, struct.error) as error:
            print(f"질문을 읽는 중 오류: {error}", flush=True)
