import os
import logging
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import requests

from sites.kaggle import extract_competitions as extract_kaggle, build_discord_message as build_kaggle_msg
from sites.devEvent import extract_competitions as extract_devEvent, build_discord_message as build_devEvent_msg
from sites.dacon import extract_competitions as extract_dacon, build_discord_message as build_dacon_msg
from sites.contestKorea import extract_competitions as extract_contestKorea, build_discord_message as build_contestKorea_msg


# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment():
    """
    .env 파일에서 환경변수 불러오기
    """
    load_dotenv()
    discord_url = os.getenv("DISCORD_URL")
    if not discord_url:
        logging.error("환경변수에 DISCORD_URL이 존재하지 않습니다.")
        raise EnvironmentError("DISCORD_URL not found in environment variables.")
    return discord_url

def send_discord_message(webhook_url, content):
    """
    디스코드 웹훅을 통해 메시지 전송
    """
    data = {
        "content": content,
    }
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204:
            logging.error(f"디스코드 메시지 전송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"디스코드 메시지 전송 중 예외 발생: {e}")



def main():
    # .env에서 환경변수 로딩 (디스코드 URL)
    try:
        discord_webhook_url = load_environment()
    except EnvironmentError as e:
        logging.critical(e)
        return

    # Playwright 실행 및 대회 정보 수집 후 전송
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # 모든 사이트에 대해 대회 수집 및 메시지 생성
        for extract_fn, build_msg_fn, site_name in [
                (extract_devEvent, build_devEvent_msg, "devEvent"),
                (extract_kaggle, build_kaggle_msg, "Kaggle"),
                (extract_contestKorea, build_contestKorea_msg, "contestKorea"),
                (extract_dacon, build_dacon_msg, "DACON"),
            ]:
                try:
                    logging.info(f"=== {site_name} 시작 ===")
                    competitions = extract_fn(page)
                    logging.info(f"{site_name}에서 {len(competitions)}개 추출됨")

                    for i in range(0, len(competitions), 8):
                        chunk = competitions[i:i+8]
                        message = build_msg_fn(chunk, first_chunk=(i == 0))
                        logging.info(f"[{site_name}] {i}~{i+len(chunk)}개 메시지:\n{message}")
                        send_discord_message(discord_webhook_url, message)

                except Exception as e:
                    logging.error(f"{site_name} 처리 중 오류 발생: {e}")

        browser.close()

    logging.info("모든 디스코드 메시지 전송 완료.")

if __name__ == "__main__":
    main()
