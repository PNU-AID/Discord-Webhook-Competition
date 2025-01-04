# 대회 알림 봇 (Discord Webhook)

이 스크립트는 [Kaggle](https://www.kaggle.com/competitions?listOption=active&sortOption=newest) 페이지에서 진행중인 대회를 스크래핑하여 Discord Webhook을 통해 특정 Discord 채널로 알림을 전송합니다.

---

## 기능

- Kaggle 페이지에서 진행 중인 대회를 스크래핑.
- 대회 제목, 부제목, 링크, 상금, 종료일 등의 정보를 Git Action을 사용하여 Discord로 전송.
- 환경 변수로 간단히 Discord URL 설정 가능.

## 출력 예시

### 행사가 있는 경우

```
## AI Model Competition
****
링크: https://example.com/competition-link
상금: $1,225,000
종료일: 2025. 3. 13. 오전 8시 59분 0초 GMT+9

### AID Jiokcamp
https://example.com/competition-link2
상금: $50,000
종료일: On going
```

### 행사가 없는 경우

```
## 진행중인 대회가 없습니다.
```

## 요구 사항

- Python 3.7 이상
- playwright
- python-dotenv
- requests
