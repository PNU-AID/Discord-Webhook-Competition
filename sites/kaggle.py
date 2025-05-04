import time
import logging
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from model import is_ai_related

def format_deadline_text(deadline_text):
    """
    마감일 텍스트를 포맷팅. (예: YYYY년 M월 D일 요일 HH:MM:SS)
    """
    if deadline_text == "Ongoing":
        return deadline_text

    if deadline_text.startswith("Deadline: "):
        # date_text = date_text.rsplit(' GMT', 1)[0]
        # date_text = date_text.replace("오전", "AM").replace("오후", "PM")
        # date_text = re.sub(r"(\D)(\d)(?=\.)", r"\g<1>0\g<2>", date_text)

        try:
            date_text = deadline_text.replace("Deadline: ", "").strip()
            # 존재하는 텍스트를 datetime object로 파싱
            # deadline = datetime.strptime(date_text, "%Y. %m. %d. %I시 %M분 %S초 %p") # GMT%z  %p
            
            # datetime object를 가독성이 좋게 다시 포맷팅
            # formatted_deadline = deadline.strftime("%Y년 %m월 %d일 %A %H:%M:%S")
            return date_text # formatted_deadline
        except ValueError as e:
            logging.error(f"마감일 텍스트 파싱 오류: {date_text} - {e}")
            return deadline_text
        
    # 형식이 맞지 않으면 원문 그대로 반환
    return deadline_text

def extract_competition_info(node):
    """
    개별 대회의 상세 정보 추출
    """
    try:
        # 대회 제목, 설명, 상금 추출
        title = node.query_selector("div > a > div > div:nth-of-type(2) > div:nth-of-type(1)").text_content().strip() # [class^='sc-eauhAA']
        desc = node.query_selector("div > a > div > div:nth-of-type(2) > span:nth-of-type(1)").text_content().strip() # [class^='sc-geXuza']
        prize = node.query_selector("div > div > div > div").text_content().strip() # [class^='sc-eauhAA hnTMYu']
        # logging.info(f"{title}, {desc}, {prize}")
        
        # AI 관련 아니면 제외
        # if not is_ai_related(title, desc):
        #     return None  
        
        hover_element = node.query_selector("div > a > div > div:nth-of-type(2) > span:nth-of-type(2) > span > span")
        hover_element.hover()
        time.sleep(0.5) # 첫 번째 요소에 hover가 적용이 안되는 문제 fix
        
        deadline_text = hover_element.evaluate(
            """(hoverElement) => {
                const rect = hoverElement.getBoundingClientRect();
                const element = document.elementFromPoint(
                    rect.left + rect.width / 2,
                    rect.top + rect.height / 2
                );
                return element?.innerText || '';
            }""",
            hover_element
        ).strip()
        # logging.info(f"{deadline_text}")
        deadline = format_deadline_text(deadline_text)
        
        # 대회 상세 페이지 링크 추출
        url = "<https://www.kaggle.com" + node.query_selector("div > a").get_attribute("href") + ">" # [class^='sc-lgprfV']

        return {
            "title": title,
            "desc": desc,
            "prize": prize,
            "deadline": deadline,
            "url": url
        }

    except PlaywrightTimeoutError:
        logging.error(f"Kaggle: 대회 상세정보 로딩 타임아웃 발생: {url}")
    except Exception as e:
        logging.error(f"Kaggle: 대회 정보 추출 중 오류 발생: {e}")
    return None

def extract_competitions(page):
    """
    Kaggle 웹페이지에서 대회 정보를 추출
    """
    competitions = []
    try:
        # 대회 페이지로 이동
        web_url = "https://www.kaggle.com/competitions?listOption=active&page=1"
        logging.info(f"Navigating to {web_url}")
        page.goto(web_url, timeout=60000)
        page.wait_for_selector("div[data-testid='list-view']", timeout=30000)
        
        # 대회들이 완전히 로드되도록 잠시 대기
        time.sleep(3)

        # 대회 노드 요소들 가져오기
        competition_nodes = page.query_selector_all("#site-content [class^='MuiListItem-root MuiListItem-gutters']")
        logging.info(f"Kaggle: {len(competition_nodes)}개의 대회 노드를 찾았습니다.")

        # 앞 8개만 처리
        for node in competition_nodes[:8]:
            info = extract_competition_info(node)
            if info is None:
                continue
            
            competitions.append(info)

    except PlaywrightTimeoutError:
        logging.error("Kaggle: 대회 페이지 로딩 타임아웃 발생")
    except Exception as e:
        logging.error(f"Kaggle: 예상치 못한 에러: {e}")
        
    logging.info(f"Kaggle: 최종 필터링된 대회 수: {len(competitions)}")
    return competitions

def build_discord_message(competitions, first_chunk=True):
    """
    대회 리스트를 디스코드 메시지 형식으로 변환
    """
    if not competitions:
        return "## 🔤 Kaggle에 올라온 진행 중인 대회가 없습니다. 🔤\n"
    
    message = ""
    if first_chunk:
        message += "# 🔤 Kaggle: 진행 중인 대회 🔤\n"
        
    for competition in competitions:
        message += (
            f"## {competition['title']}\n"
            f"* **{competition['desc']}**\n"
            f"* {competition['url']}\n"
            f"* 상금: {competition['prize']}\n"
            f"* 종료일: {competition['deadline']}\n\n"
        )
    return message