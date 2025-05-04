import logging
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from model import is_ai_related

def extract_competition_info(node):
    """
    개별 대회의 상세 정보 추출
    """
    try:
        # 대회 진행상태 추출
        state_element = node.query_selector("[class='dday']") 
        state = state_element.text_content().strip() if state_element else "No State"
        # 현재 진행 중인 대회가 아니면 스킵
        if state not in ['참가신청중', '미참가']:
            return None
        
        # 대회 제목 추출
        title_element = node.query_selector("[class='name ellipsis']") 
        title = title_element.text_content().strip() if title_element else "No Title"

        # 대회 정보 추출
        desc_element = node.query_selector("[class='info2 ellipsis keyword']")
        desc = desc_element.text_content().strip() if desc_element else "No Description"

        # 대회 URL 추출
        link_element = node.query_selector("a")
        url = "<https://dacon.io" + link_element.get_attribute("href").strip() + ">" if link_element else "No URL"

        # 대회 날짜 추출
        deadline_element = node.query_selector("[class='d-day']")
        deadline = deadline_element.text_content().strip() if deadline_element else "No Deadline"

        # 대회 상금 추출
        prize_element = node.query_selector("[class='price']")
        prize = prize_element.text_content().strip() if prize_element else "No Price"

        # AI 관련 아니면 제외
        # if not is_ai_related(title, desc):
        #     return None  
        
        return {
            "title": title,
            "desc": desc,
            "prize": prize,
            "deadline": deadline,
            "url": url
        }

    except PlaywrightTimeoutError:
        logging.error(f"DACON: 대회 상세정보 로딩 타임아웃 발생: {url}") # {url}
    except Exception as e:
        logging.error(f"DACON: 대회 정보 추출 중 오류 발생: {e}") # {url}
    return None

def extract_competitions(page):
    """
    DACON 웹페이지에서 대회 정보를 추출
    """
    competitions = []

    try:
        # 대회 페이지로 이동
        web_url = "https://dacon.io/competitions"
        logging.info(f"Navigating to {web_url}")
        page.goto(web_url, timeout=60000)
        page.wait_for_selector("[class^='v-main']", timeout=30000) 
        
        # 대회들이 완전히 로드되도록 잠시 대기
        time.sleep(3)
        
        # 대회 노드 요소들 가져오기
        competition_nodes = page.query_selector_all("[class='comp']")
        logging.info(f"DACON: {len(competition_nodes)}개의 대회 노드를 찾았습니다.")

        for node in competition_nodes:
            info = extract_competition_info(node)
            if info is None:
                continue

            competitions.append(info)

    except PlaywrightTimeoutError:
        logging.error("DACON: 대회 페이지 로딩 타임아웃 발생")
    except Exception as e:
        logging.error(f"DACON: 예상치 못한 에러: {e}")
        
    logging.info(f"DACON: 최종 필터링된 대회 수: {len(competitions)}")
    return competitions

def build_discord_message(competitions, first_chunk=True):
    """
    대회 리스트를 디스코드 메시지 형식으로 변환
    """
    if not competitions:
        return "## DACON에 올라온 진행 중인 대회가 없습니다."
    
    message = ""
    if first_chunk:
        message += "# DACON: 진행 중인 대회\n"
        
    for competition in competitions:
        message += (
            f"## {competition['title']}\n"
            f"* **{competition['desc']}**\n"
            f"* {competition['url']}\n"
            f"* 상금: {competition['prize']}\n"
            f"* 종료일: {competition['deadline']}\n\n"
        )
    return message