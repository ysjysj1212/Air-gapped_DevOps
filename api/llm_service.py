# requests 라이브러리를 임포트해서 HTTP 요청을 보낼 수 있게 함
import requests

# Ollama API 서버의 주소를 변수에 저장함
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# 사용할 AI 모델의 이름을 변수에 저장함
MODEL_NAME = "llama3"


# Ollama 인공지능에게 질문을 보내고 답변을 받아오는 함수를 정의함
def ask_ollama(prompt):
    # 함수에 받은 질문(prompt)을 처리함
    
    try:
        # 요청할 데이터를 딕셔너리 형태로 만들어서 저장함
        # model: 사용할 AI 모델 이름
        # prompt: 사용자가 던진 질문
        # stream: false로 설정해서 한 번에 전체 답변을 받도록 함
        request_data = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        
        # Ollama API에 POST 요청을 보내고 응답을 받아서 response 변수에 저장함
        response = requests.post(OLLAMA_API_URL, json=request_data)
        
        # 응답이 정상적으로 왔는지 확인함 (상태 코드가 200이면 성공)
        response.raise_for_status()
        
        # 응답 데이터를 JSON 형식으로 변환해서 저장함
        result = response.json()
        
        # JSON 데이터에서 "response" 키의 값(실제 답변)을 추출해서 반환함
        return result.get("response", "답변 없음")
    
    # 만약 Ollama 서버에 연결할 수 없거나 다른 에러가 발생하면 이 블록이 실행됨
    except requests.exceptions.RequestException as error:
        # 에러가 발생했다는 메시지를 출력함
        print("오류 발생")
        
        # 상세한 에러 정보를 콘솔에 출력함 (개발할 때 디버깅용)
        print(f"상세 오류: {error}")
        
        # None을 반환해서 실패했다는 것을 표현함
        return None


# 이 파일이 직접 실행될 때만 아래 코드가 동작함 (import 될 때는 실행 안 됨)
if __name__ == "__main__":
    # 테스트용 질문을 변수에 저장함
    test_prompt = "Python이란 무엇인가?"
    
    # ask_ollama 함수에 질문을 보내고 답변을 받아서 저장함
    answer = ask_ollama(test_prompt)
    
    # 받아온 답변이 None이 아니라면 (즉, 성공했다면) 답변을 출력함
    if answer:
        print(f"질문: {test_prompt}")
        print(f"답변: {answer}")
