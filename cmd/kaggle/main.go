package main

import (
	"context"
	"fmt"
	"log"
	"strings"
	"time"

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

func getCompetitionList(body *goquery.Document) []string {
	url_list := make([]string, 0, 21)
	docs := body.Find("div[data-testid='list-view'] div ul li div a")
	for _, node := range docs.Nodes {
		url_list = append(url_list, node.Attr[0].Val)
	}
	return url_list
}

func getCompetitionInfo(body *goquery.Document) {
	title_elem := body.Find("h1")
	title := title_elem.Text()
	desc := title_elem.Nodes[0].NextSibling.FirstChild.FirstChild.Data

	info_div := body.Find("div.sc-iMXWWd.eEROHA:nth-child(2) div div p:first-child")
	prize := info_div.Text()

	var start_date string
	var deadline string
	body.Find("div.sc-gnQwKE.bwYRmi span.sc-cyZbeP.hwHu").Each(func(i int, s *goquery.Selection) {
		hasChild := len(s.Children().Nodes)
		var date_string string
		if hasChild == 1 {
			date_string, _ = s.Children().First().Attr("title")
		} else {
			date_string = s.Text()
		}

		if i == 0 {
			start_date = date_string
		} else {
			deadline = date_string
		}
	})

	image_elem := body.Find("img.sc-emfenM.sc-kNnbAW.biNcPW.jBmLfK")
	image_url, exists := image_elem.Attr("src")
	if !exists {
		image_url = "No image"
	}

	fmt.Println(title, "|", desc, "|", prize, "|", start_date, "|", deadline, "|", image_url)
}

func main() {
	var competition_url_list []string
	var base_url string = "https://www.kaggle.com"
	var base_url_comp string = "https://www.kaggle.com/competitions"

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
		chromedp.WaitEnabled("button.sc-kHoYCX.bTaTMz"),
		chromedp.Click("button.sc-kHoYCX.bTaTMz", chromedp.BySearch), // click "All competition" button
		chromedp.WaitEnabled("button[aria-label='more_horiz']"),      // wait for the comptetion list to be loaded
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

		getCompetitionInfo(doc)
	}
}
