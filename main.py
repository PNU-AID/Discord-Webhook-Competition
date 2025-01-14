import os
import logging
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment():
    """
    Load environment variables from .env file.
    """
    load_dotenv()
    discord_url = os.getenv("DISCORD_URL")
    if not discord_url:
        logging.error("DISCORD_URL not found in environment variables.")
        raise EnvironmentError("DISCORD_URL not found in environment variables.")
    return discord_url

def send_discord_message(webhook_url, content):
    """
    Send a message to Discord using the provided webhook URL.
    """
    data = {
        "content": content,
    }
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204:
            logging.error(f"Failed to send Discord message: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Exception while sending Discord message: {e}")

def extract_competitions(page):
    """
    Extract competition data from Kaggle's webpage.
    """
    competitions = []
    try:
        # Navigate to the events page
        web_url = "https://www.kaggle.com/competitions?listOption=active&sortOption=newest"
        logging.info(f"Navigating to {web_url}")
        page.goto(web_url, timeout=60000)
        page.wait_for_selector("div[data-testid='list-view']", timeout=30000)
        
        # Wait additional time to ensure all events are loaded
        time.sleep(3)

        # Get all competition containers
        competition_nodes = page.query_selector_all("#site-content [class^='MuiListItem-root MuiListItem-gutters']")
        logging.info(f"Found {len(competition_nodes)} competition nodes.")

        for node in competition_nodes:
            competitions.append(extract_competition_info(node))

    except PlaywrightTimeoutError:
        logging.error("Timeout while loading the Kaggle competition page.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        
    logging.info(f"Total filtered events: {len(competitions)}")
    return competitions

def format_deadline_text(deadline_text):
    """
    Format the deadline_text based on its content. "YYYY년 M월 D일 요일 HH:MM:SS"
    """
    if deadline_text == "Ongoing":
        return deadline_text

    if deadline_text.startswith("Deadline: "):
        # date_text = date_text.rsplit(' GMT', 1)[0]
        # date_text = date_text.replace("오전", "AM").replace("오후", "PM")
        # date_text = re.sub(r"(\D)(\d)(?=\.)", r"\g<1>0\g<2>", date_text)

        try:
            date_text = deadline_text.replace("Deadline: ", "").strip()
            
            # Parse the remaining text into a datetime object
            # deadline = datetime.strptime(date_text, "%Y. %m. %d. %I시 %M분 %S초 %p") # GMT%z  %p
            
            # Format the datetime object into the desired format
            # formatted_deadline = deadline.strftime("%Y년 %m월 %d일 %A %H:%M:%S")
            return date_text # formatted_deadline
        except ValueError as e:
            # Handle parsing errors gracefully
            logging.error(f"Error parsing deadline text: {date_text} - {e}")
            return deadline_text
        
    # Return the text as is if it doesn't match the expected format
    return deadline_text
    
def extract_competition_info(node):
    """
    Extract detailed information about a specific competition.
    """
    try:
        # Extract competition details
        title = node.query_selector("[class^='sc-eauhAA']").text_content().strip()
        desc = node.query_selector("[class^='sc-geXuza']").text_content().strip()
        prize = node.query_selector("[class^='sc-eauhAA hnTMYu']").text_content().strip()
        
        # Start Data is not exist on web site
        # start_date = node.query_selector_all("span[title]")[1].get_attribute("title").strip()
        
        hover_element = node.query_selector("[class^='sc-bSficL'] span")
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
        
        url = "https://www.kaggle.com" + node.query_selector("[class^='sc-lgprfV']").get_attribute("href")

        return {
            "title": title,
            "desc": desc,
            "prize": prize,
            # "start_date": start_date,
            "deadline": deadline,
            "url": url
        }

    except PlaywrightTimeoutError:
        logging.error(f"Timeout while loading competition details: {url}") # {url}
    except Exception as e:
        logging.error(f"Error extracting competition info from : {e}") # {url}
    return None

def build_discord_message(competitions):
    """
    Build the Discord message content from the list of competitions.
    """
    if not competitions:
        return "## 진행중인 대회가 없습니다."
    
    message = ""
    for competition in competitions:
        # start_date = competition["start_date"]
        # deadline = competition["deadline"]
        message += (
            f"## {competition['title']}\n"
            f"**{competition['desc']}**\n"
            f"{competition['url']}\n"
            f"상금: {competition['prize']}\n"
            # f"시작일: {start_date}\n"
            f"종료일: {competition['deadline']}\n\n"
        )
    return message

def main():
    # Load environment variables (= Discord URL)
    try:
        discord_webhook_url = load_environment()
    except EnvironmentError as e:
        logging.critical(e)
        return

    # Initialize Playwright and extract competitions
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        competitions = extract_competitions(page)
        browser.close()
        logging.info(f"Extracted {len(competitions)} competition nodes.")

    # Build and send the message content to Discord    
    for i in range(0, len(competitions), 8):
        competition_chunk = competitions[i:i+8]
        message_content = build_discord_message(competition_chunk)
        # logging.info(message_content)
        send_discord_message(discord_webhook_url, message_content)
        logging.info(f"Constructed Discord message for {i} to {i+8}.")
    logging.info("Discord message sent successfully.")

if __name__ == "__main__":
    main()
