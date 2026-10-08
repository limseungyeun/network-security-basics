"""수업용 DNS 클라이언트: 내 PC의 local_dns.py에 질문함"""

import socket

HOST = "127.0.0.1"  # 서버가 실행 중인 내 컴퓨터
PORT = 15301  # local_dns.py의 PORT와 같아야 함.

# classroom.test의 IPv4 주소(A 레코드)를 묻는 DNS 질문을 만듬
# DNS는 정해진 형식의 바이트 데이터를 주고받음
# 첫 줄은 요청 ID/헤더, 다음 두 줄은 이름, 마지막 줄은 질문 종류/클래스입니다.
request = bytes.fromhex(
    "123401000001000000000000"  # DNS 헤더: 요청 ID(1234), 일반 질문, 질문 개수 1개 등을 나타냄
    "09636c617373726f6f6d"  # 'classroom': 글자 수 9개(09) + 각 글자를 바이트로 표현한 값
    "0474657374"     # 'test': 글자 수 4개(04) + 각 글자를 바이트로 표현한 값
    "0000010001"     # 00: 도메인 이름의 끝
                     # 0001: IPv4 주소를 묻는 A 레코드
                     # 0001: 인터넷에서 사용하는 IN 클래스
)

# AF_INET: IPv4 주소를 사용합니다.
# SOCK_DGRAM: UDP 방식으로 통신합니다.
# with를 사용하면 작업이 끝난 뒤 소켓이 자동으로 닫힙니다.
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
    client.settimeout(3)  # 3초 동안 답이 없으면 계속 기다리지 않음
    client.sendto(request, (HOST, PORT))  # 서버로 질문 보내기
    print(f"질문 전송: {HOST}:{PORT}")  # 즉, 내 컴퓨터의 로컬 DNS 서버에 질문함

    try:
        response, address = client.recvfrom(512)  # 서버의 응답 기다리기
        # response: 서버가 보낸 데이터
        # address: 답을 보낸 서버의 IP와 포트
        # 512: 한 번에 받을 데이터의 최대 크기(바이트)
        
        print("응답 받음!!!")
        print("보낸 서버:", address)
        
         # 받은 데이터가 이번 질문에 대한 정상 응답인지 간단히 확인
        if (
            len(response) >= 4                  # 최소한 확인할 바이트가 있는가?
            and response[:2] == request[:2]      # 질문 ID와 응답 ID가 같은가?
            and (response[3] & 0x0F) == 0        # DNS 오류 코드가 0인가?
        ):
            # 이 수업의 정상 A 응답에서는 마지막 4바이트가 IPv4 주소임
            print("응답한 IP:", ".".join(map(str, response[-4:])))   # 각 바이트를 숫자 문자열로 바꾸고 점(.)으로 연결함
        else:
            print("예상한 형식의 응답이 아닙니다.")
    except socket.timeout:
        print("3초가 지나도 응답이 오지 않았습니다.")
