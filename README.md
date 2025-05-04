# 대회 알림 봇 (Discord Webhook)

이 스크립트는 여러 대회 페이지에서 진행중인 대회를 스크래핑하여 Discord Webhook을 통해 특정 Discord 채널로 알림을 전송합니다.

- [Kaggle](https://www.kaggle.com/competitions?listOption=active&sortOption=newest)
- [DACON](https://dacon.io/competitions)
- [devEvent](https://dev-event.vercel.app/search?type=%EB%8C%80%ED%9A%8C)
- [contestKorea](https://www.contestkorea.com/sub/list.php?int_gbn=1&Txt_bcode=030510001)

---

## 기능

- 여러 대회 사이트에서 진행 중인 대회를 스크래핑.
- 대회 제목, 부제목, 주최자, 링크, 상금, 종료일 등의 정보를 Git Action을 사용하여 Discord로 전송.
- 환경 변수로 간단히 Discord URL 설정 가능.
- Zero-shot을 사용하여 AI 관련 대회 분류 (`model.py`)
  - ※ 거의 모든 대회에서 AI를 필요로 하고, 적용 가능하기에 사용하지 않음

## 출력 예시

### 행사가 있는 경우

```
# [SITE_NAME]에서 진행 중인 대회
## AI Model Competition
****
링크: https://example.com/competition-link
상금: $1,225,000
종료일: 2025. 3. 13. 오전 8시 59분 0초 GMT+9

## AID Jiokcamp
https://example.com/competition-link2
상금: $50,000
종료일: On going
```

### 행사가 없는 경우

```
## [SITE_NAME]에 진행 중인 대회가 없습니다.
```

## 요구 사항 (pip_requirements.txt 참고)

- Python 3.7 이상
- playwright==1.52.0
- python-dotenv==1.1.0
- requests==2.32.3
- torch==2.7.0
- transformers==4.51.3 etc.

## 사용방법

1. .env에서 `DISCORD_URL` 지정
2. `python -m venv venv` 이후 가상환경 활성화
3. `pip install -r pip_requirements.txt`로 필요 라이브러리 다운로드
4. `python main.py` 실행
