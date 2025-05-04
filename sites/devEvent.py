import logging
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from model import is_ai_related

def extract_competition_info(node):
    """
    개별 대회의 상세 정보 추출
    """
    try:
        # D-day 추출
        dday_element = node.query_selector("[class^='DdayTag_tag__']") # .DdayTag_tag__6_oE7
        if not dday_element:
            logging.debug("D-Day element not found, skipping event.")
            return None
        today_text = dday_element.text_content().strip()
        # 현재 진행 중인 대회가 아니면 스킵
        if "Today" not in today_text:
            return None

        # 대회 제목 추출
        title_element = node.query_selector("[class^='Item_item__content__title__']") # .Item_item__content__title__94_8Q
        title = title_element.text_content().strip() if title_element else "No Title"

        # 대회 URL 추출
        link_element = node.query_selector("a")
        url = "<" + link_element.get_attribute("href").strip() + ">" if link_element else "No URL"

        # 대회 날짜 추출
        date_element = node.query_selector("[class^='Item_date__date__']") # .Item_date__date__CoMqV
        date_text = date_element.text_content().strip() if date_element else "No Date"

        # 대회 주체자 추출
        host_element = node.query_selector("[class^='Item_host__']") # .Item_host__3dy8_
        host_text = host_element.text_content().strip() if host_element else "No Host"

        # AI 관련 아니면 제외
        # if not is_ai_related(title, desc):
        #     return None  
        
        return {
            "title": title,
            "host": host_text,
            "date": date_text,
            "url": url
        }

    except PlaywrightTimeoutError:
        logging.error(f"devEvent: 대회 상세정보 로딩 타임아웃 발생: {url}") # {url}
    except Exception as e:
        logging.error(f"devEvent: 대회 정보 추출 중 오류 발생: {e}") # {url}
    return None

def extract_competitions(page):
    """
    Dev Event 웹페이지에서 대회 정보를 추출
    """
    competitions = []
    title_set = set()  # 중복 확인용 대회 제목 집합

    try:
        # 대회 페이지로 이동
        web_url = "https://dev-event.vercel.app/search?type=%EB%8C%80%ED%9A%8C"
        logging.info(f"Navigating to {web_url}")
        page.goto(web_url, timeout=60000)
        page.wait_for_selector("[class^='Home_section__']", timeout=30000)  # .Home_section__EaDnq
        
        # 대회들이 완전히 로드되도록 잠시 대기
        time.sleep(3)
        
        # 대회 노드 요소들 가져오기
        competition_nodes = page.query_selector_all("[class^='Item_item__container']") # .Item_item__container___T09W
        logging.info(f"devEvent: {len(competition_nodes)}개의 대회 노드를 찾았습니다.")

        for node in competition_nodes:
            info = extract_competition_info(node)
            if info is None:
                continue
                
            # 중복된 대회 발견 시 pass
            if info["title"] in title_set:
                continue

            competitions.append(info)
            title_set.add(info["title"])

    except PlaywrightTimeoutError:
        logging.error("devEvent: 대회 페이지 로딩 타임아웃 발생")
    except Exception as e:
        logging.error(f"devEvent: 예상치 못한 에러: {e}")
        
    logging.info(f"devEvent: 최종 필터링된 대회 수: {len(competitions)}")
    return competitions

def build_discord_message(competitions, first_chunk=True):
    """
    대회 리스트를 디스코드 메시지 형식으로 변환
    """
    if not competitions:
        return "## devEvent에 올라온 진행 중인 대회가 없습니다."
    
    message = ""
    if first_chunk:
        message += "# devEvent: 진행 중인 대회\n"
        
    for competition in competitions:
        message += (
            f"## {competition['title']}\n"
            f"* **{competition['host']}**\n"
            f"* {competition['url']}\n"
            f"* 대회 기간: {competition['date']}\n\n"
        )
    return message