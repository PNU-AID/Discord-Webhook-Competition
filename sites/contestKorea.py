import logging
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from model import is_ai_related

def extract_competition_info(node):
    """
    개별 대회의 상세 정보 추출
    """
    try:
        # 대회 제목 추출 (내부 <span class="txt"> 태그 사용)
        title_element = node.query_selector("div.title a span.txt")
        title = title_element.text_content().strip() if title_element else "No Title"

        # 대회 URL 추출
        link_element = node.query_selector("div.title a")
        href = link_element.get_attribute("href").strip() if link_element else None
        url = f"<https://www.contestkorea.com/sub/{href}>" if href else "No URL"
        
        # 주최 추출
        host_element = node.query_selector("ul.host > li.icon_1")
        if host_element:
            host = host_element.text_content().strip()
            host = host.replace("주최", "").replace(":", "").strip(" .:\n\t")
        else:
            host = "No Host"
            
        # 대상 추출
        target_element = node.query_selector("ul.host > li.icon_2")
        if target_element:
            target = target_element.text_content()
            target = target.replace("대상", "").replace("·", "").replace(".", "") \
                          .replace("\n", "").replace(":", "").strip()
            target = ", ".join([t.strip() for t in target.split(",") if t.strip()])
        else:
            target = "No Target"
        
        # 접수 기간
        register_element = node.query_selector("div.date-detail span.step-1")
        register = register_element.text_content().replace("접수", "").strip() if register_element else "No Register Period"

        # 심사 기간
        review_element = node.query_selector("div.date-detail span.step-2")
        review = review_element.text_content().replace("심사", "").strip() if review_element else "No Review Period"

        # 발표 날짜
        announce_element = node.query_selector("div.date-detail span.step-3")
        announce = announce_element.text_content().replace("발표", "").strip() if announce_element else "No Announcement Date"

        # D-day 값 추출
        dday_element = node.query_selector("div.d-day.orange > span.day")
        dday = dday_element.text_content().strip() if dday_element else "No D-day"

        # AI 관련 아니면 제외
        # if not is_ai_related(title, desc):
        #     return None  
        
        return {
            "title": title,
            "url": url,
            "host": host,
            "target": target,
            "register": register,
            "review": review,
            "announce": announce,
            "dday": dday
        }


    except PlaywrightTimeoutError:
        logging.error(f"Dacon: 대회 상세정보 로딩 타임아웃 발생: {url}") # {url}
    except Exception as e:
        logging.error(f"Dacon: 대회 정보 추출 중 오류 발생: {e}") # {url}
    return None

def extract_competitions(page):
    """
    Dacon 웹페이지에서 대회 정보를 추출
    """
    competitions = []

    try:
        # 대회 페이지로 이동
        web_url = "https://www.contestkorea.com/sub/list.php?int_gbn=1&Txt_bcode=030510001"
        logging.info(f"Navigating to {web_url}")
        page.goto(web_url, timeout=60000)
        page.wait_for_selector("[class='conditional_search']", timeout=30000) 
        
        # '대학생' 체크 using ID
        page.check("#Txt_code16")  
        # '선택된 조건 검색' 버튼 클릭
        page.click("#btn_search1")
        page.wait_for_load_state("load")
        page.wait_for_selector("[class='clfx mb_20']", timeout=30000) 
        # '접수중' 탭 클릭
        page.locator("button.btn_sort").filter(has_text="접수중").click()
        page.wait_for_timeout(20000)
        
        # 대회 노드 요소들 가져오기
        competition_nodes = page.query_selector_all("div.list_style_2 > ul > li")
        logging.info(f"contestKorea: {len(competition_nodes)}개의 대회 노드를 찾았습니다.")

        # 앞 8개만 처리
        for node in competition_nodes[:8]:
            info = extract_competition_info(node)
            if info is None:
                continue

            competitions.append(info)

    except PlaywrightTimeoutError:
        logging.error("contestKorea: 대회 페이지 로딩 타임아웃 발생")
    except Exception as e:
        logging.error(f"contestKorea: 예상치 못한 에러: {e}")
        
    logging.info(f"contestKorea: 최종 필터링된 대회 수: {len(competitions)}")
    return competitions

def build_discord_message(competitions, first_chunk=True):
    """
    대회 리스트를 디스코드 메시지 형식으로 변환
    """
    if not competitions:
        return "## contestKorea에 올라온 진행 중인 대회가 없습니다."
    
    message = ""
    if first_chunk:
        message += "# contestKorea: 진행 중인 대회\n"
        
    for competition in competitions:
        message += (
            f"## {competition['title']}\n"
            f"* **{competition['host']}**\n"
            f"* {competition['url']}\n"
            # f"* 대상: {competition['target']}\n"
            f"* 접수: {competition['register']}\n"
            f"* 심사: {competition['review']}\n"
            f"* 발표: {competition['announce']}\n\n"
            # f"* 일정({competition['dday']}): 접수-{competition['register']}, 심사-{competition['review']}, 발표-{competition['announce']}\n\n"
        )
    return message