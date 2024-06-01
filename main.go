package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
	"github.com/disgoorg/disgo/webhook"
	"github.com/joho/godotenv"
)

type competitionInfo struct {
	title      string
	desc       string
	prize      string
	start_date string
	deadline   string
	image_url  string
}

func (info competitionInfo) isAvailable() bool {
	if !strings.Contains(info.start_date, "GMT") || !strings.Contains(info.deadline, "GMT") {
		return false
	}
	return true
}

func getCompetitionList(body *goquery.Document) []string {
	url_list := make([]string, 0, 21)
	docs := body.Find("div[data-testid='list-view'] div ul li div a")
	docs.Each(func(i int, s *goquery.Selection) {
		attr_url, exist := s.Attr("href")
		if exist {
			url_list = append(url_list, attr_url)
		}
	})
	return url_list
}

func getCompetitionInfo(body *goquery.Document) competitionInfo {
	title_elem := body.Find("h1")
	title := title_elem.Text()
	desc := title_elem.Nodes[0].NextSibling.FirstChild.FirstChild.Data

	info_div := body.Find("div[data-testid='competition-detail-render-tid']>div>div:nth-child(6)>div:nth-child(4)>div>div:nth-child(2)>div>div>p:first-child")
	prize := info_div.Text()

	var start_date string
	var deadline string
	body.Find("span[title]").Each(func(i int, s *goquery.Selection) {
		attr_title, exist := s.Attr("title")
		if exist {
			if i == 1 {
				start_date = attr_title
			} else if i == 2 {
				deadline = attr_title
			}
		}
	})

	image_elem := body.Find("div[wrap='hide'] img")
	image_url, exists := image_elem.Attr("src")
	if !exists {
		image_url = "No image"
	}

	// fmt.Println(title, "|", desc, "|", prize, "|", start_date, "|", deadline, "|", image_url)
	return competitionInfo{title: title, desc: desc, prize: prize, start_date: start_date, deadline: deadline, image_url: image_url}
}

func formatTimeString(timestring string) string {
	string_arr := strings.Fields(timestring)
	weekday := string_arr[0]
	month := string_arr[1]
	day := string_arr[2]
	year := string_arr[3]
	time := string_arr[4]

	switch month {
	case "Jan":
		month = "1"
	case "Feb":
		month = "2"
	case "Mar":
		month = "3"
	case "Apr":
		month = "4"
	case "May":
		month = "5"
	case "Jun":
		month = "6"
	case "Jul":
		month = "7"
	case "Aug":
		month = "8"
	case "Sep":
		month = "9"
	case "Oct":
		month = "10"
	case "Nov":
		month = "11"
	case "Dec":
		month = "12"
	default:
		month = ""
	}

	switch weekday {
	case "Mon":
		weekday = "월"
	case "Tue":
		weekday = "화"
	case "Wed":
		weekday = "수"
	case "Thu":
		weekday = "목"
	case "Fri":
		weekday = "금"
	case "Sat":
		weekday = "토"
	case "Sun":
		weekday = "일"
	default:
		weekday = ""
	}

	return year + "년 " + month + "월 " + day + "일 " + weekday + "요일 " + time
}

func buildDiscordMessage(info competitionInfo, competitionUrl string) string {
	title := info.title
	desc := info.desc
	prize := info.prize
	start_date := info.start_date
	deadline := info.deadline
	// image_url := info.image_url

	message := "## " + title + "\n**" + desc + "**\n" + "링크 : " + competitionUrl + "\n상금 : " + prize + "\n시작일 : " + formatTimeString(start_date) + "\n종료일 : " + formatTimeString(deadline)

	return message
}

func main() {
	env_err := godotenv.Load()
	if env_err != nil {
		log.Fatal("Error loading .env file")
	}
	discord_url := os.Getenv("DISCORD_URL")
	client, webhook_err := webhook.NewWithURL(discord_url)
	if webhook_err != nil {
		log.Fatal("Error in discord_url")
	}

	var competition_url_list []string
	var base_url string = "https://www.kaggle.com"
	var base_url_comp string = "https://www.kaggle.com/competitions?listOption=active&sortOption=newest"

	// use when debugging

	// opts := append(chromedp.DefaultExecAllocatorOptions[:],
	// 	chromedp.Flag("headless", false),
	// )

	// allocCtx, cancel := chromedp.NewExecAllocator(context.Background(), opts...)
	// defer cancel()

	// ctx, cancel := chromedp.NewContext(allocCtx, chromedp.WithLogf(log.Printf))
	// defer cancel()

	ctx, cancel := chromedp.NewContext(context.Background())
	defer cancel()
	ctx, cancel = context.WithTimeout(ctx, 60*time.Second)
	defer cancel()

	var renderedHTML string

	err := chromedp.Run(
		ctx,
		chromedp.Navigate(base_url_comp),
		chromedp.WaitEnabled("button[aria-label='more_horiz']"), // wait for the comptetion list to be loaded
		chromedp.OuterHTML("html", &renderedHTML, chromedp.ByQuery),
	)
	if err != nil {
		log.Fatal(err)
	}

	doc, err := goquery.NewDocumentFromReader(strings.NewReader(renderedHTML))

	if err != nil {
		log.Fatal(err)
	}

	competition_url_list = getCompetitionList(doc)
	for i, url := range competition_url_list {
		competition_url_list[i] = base_url + url
	}

	var discord_content_message string
	var message_slice []string

	for _, url := range competition_url_list {
		var renderedCompetition string
		err := chromedp.Run(
			ctx,
			chromedp.Navigate(url),
			chromedp.OuterHTML("div[data-testid='competition-detail-render-tid']", &renderedCompetition, chromedp.ByQuery),
		)
		if err != nil {
			log.Fatal(err)
		}

		doc, err := goquery.NewDocumentFromReader(strings.NewReader(renderedCompetition))
		if err != nil {
			log.Fatal(err)
		}

		content := getCompetitionInfo(doc)
		if content.isAvailable() {
			fmt.Println(content.title, "|", content.desc, "|", content.prize, "|", content.start_date, "|", content.deadline, "|", content.image_url)
			// fmt.Println(content.title)
		} else {
			fmt.Println("end of available competition")
			break
		}

		content_message := buildDiscordMessage(content, url)
		if utf8.RuneCountInString(discord_content_message)+utf8.RuneCountInString(content_message) > 2000 {
			message_slice = append(message_slice, discord_content_message)
			discord_content_message = ""
		}
		discord_content_message += content_message + "\n\n"
		// fmt.Println(content_message)
	}
	message_slice = append(message_slice, discord_content_message)

	for _, message := range message_slice {
		_, err_dis := client.CreateContent(message)
		if err_dis != nil {
			log.Fatal(err_dis)
		}
	}
}
