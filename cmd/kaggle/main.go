package main

import (
	"context"
	"fmt"
	"log"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"github.com/chromedp/chromedp"
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
	// const layout_long = "Mon Jan 02 2006 15:04:05 GMT+0900 (한국 표준시)"
	// const layout_short = "Feb 1, 2021"

	// start_date := info.start_date
	// end_date := info.deadline

	// var start_datetime time.Time
	// var end_datetime time.Time
	// var err error

	// if strings.Contains(start_date, "GMT") {
	// 	start_datetime, err = time.Parse(layout_long, start_date)
	// } else {
	// 	start_datetime, err = time.Parse(layout_short, start_date)
	// }
	// if err != nil {
	// 	fmt.Println("Can't parse start date. (" + start_date + ")")
	// }

	// if strings.Contains(end_date, "GMT") {
	// 	end_datetime, err = time.Parse(layout_long, end_date)
	// } else {
	// 	end_datetime, err = time.Parse(layout_short, end_date)
	// }
	// if err != nil {
	// 	fmt.Println("Can't parse start date. (" + start_date + ")")
	// }

	// fmt.Println(start_datetime)
	// fmt.Println(end_datetime)

	// return true
}

func getCompetitionList(body *goquery.Document) []string {
	url_list := make([]string, 0, 21)
	docs := body.Find("div[data-testid='list-view'] div ul li div a")
	for _, node := range docs.Nodes {
		url_list = append(url_list, node.Attr[1].Val)
	}
	return url_list
}

func getCompetitionInfo(body *goquery.Document) competitionInfo {
	title_elem := body.Find("h1")
	title := title_elem.Text()
	desc := title_elem.Nodes[0].NextSibling.FirstChild.FirstChild.Data

	// info_div := body.Find("div.sc-iMXWWd.eEROHA:nth-child(2) div div p:first-child")
	info_div := body.Find("div[data-testid='competition-detail-render-tid']>div>div:nth-child(6)>div:nth-child(4)>div>div:nth-child(2)>div>div>p:first-child")
	prize := info_div.Text()

	var start_date string
	var deadline string
	body.Find("span[title]").Each(func(i int, s *goquery.Selection) {
		fmt.Print(i)
		attr_title, _ := s.Attr("title")
		fmt.Println(" " + attr_title)
	})
	// body.Find("div#abstract>div:nth-child(2)>div>div>div span.sc-cyZbeP.hwHu").Each(func(i int, s *goquery.Selection) {
	// 	hasChild := len(s.Children().Nodes)
	// 	var date_string string
	// 	if hasChild == 1 {
	// 		date_string, _ = s.Children().First().Attr("title")
	// 	} else {
	// 		date_string = s.Text()
	// 	}

	// 	if i == 0 {
	// 		start_date = date_string
	// 	} else if i == 1 {
	// 		deadline = date_string
	// 	}
	// })

	image_elem := body.Find("div[wrap='hide'] img")
	image_url, exists := image_elem.Attr("src")
	if !exists {
		image_url = "No image"
	}

	fmt.Println(title, "|", desc, "|", prize, "|", start_date, "|", deadline, "|", image_url)
	return competitionInfo{title: title, desc: desc, prize: prize, start_date: start_date, deadline: deadline, image_url: image_url}

}

func main() {
	// discord_url := "https://discord.com/api/webhooks/1218448415738822726/K57_CJ_NhMkkSQ_JDcdQFp4ee7YCd5LveMbhLhp5Er1gHB6zFIh7t1U2X8ze8BM6ie-D"
	// client, webhook_err := webhook.NewWithURL(discord_url)
	// if webhook_err != nil {
	// 	log.Fatal("Error in discord_url")
	// }

	var competition_url_list []string
	var base_url string = "https://www.kaggle.com"
	var base_url_comp string = "https://www.kaggle.com/competitions"

	// use when debugging

	opts := append(chromedp.DefaultExecAllocatorOptions[:],
		chromedp.Flag("headless", false),
	)

	allocCtx, cancel := chromedp.NewExecAllocator(context.Background(), opts...)
	defer cancel()

	ctx, cancel := chromedp.NewContext(allocCtx, chromedp.WithLogf(log.Printf))
	defer cancel()

	// ctx, cancel := chromedp.NewContext(context.Background())
	// defer cancel()
	// ctx, cancel = context.WithTimeout(ctx, 60*time.Second)
	// defer cancel()

	var renderedHTML string

	err := chromedp.Run(
		ctx,
		chromedp.Navigate(base_url_comp),
		chromedp.WaitEnabled("button.sc-jKfPkT.jycYRR"),
		chromedp.Click("button.sc-jKfPkT.jycYRR", chromedp.BySearch), // click "All competition" button
		chromedp.WaitEnabled("button[title='Filters']"),
		chromedp.Click("button[title='Filters']"),
		chromedp.WaitEnabled("button[aria-label='Active']"),
		chromedp.Click("button[aria-label='Active']"),
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
			fmt.Println(content.title)
		} else {
			fmt.Println("end of available competition")
			// break
		}

		// content_message := "## " + content.title

		// fmt.Println(content_message)

		// _, err_dis := client.CreateContent(content_message)
		// if err_dis != nil {
		// 	log.Fatal(err_dis)
		// }
	}
}
