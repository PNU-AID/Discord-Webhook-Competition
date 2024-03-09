package main

import (
	"fmt"

	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly"
	"golang.org/x/net/html"
)

type competitionDesc struct {
	name    string
	keyword string
}

func extract_picinfo(div *html.Node) string {
	attrs := div.FirstChild.Attr
	var img_url string
	for _, attr_name := range attrs {
		if attr_name.Key == "src" {
			img_url = attr_name.Val
		}
	}

	return img_url
}

func extract_description(div *html.Node) *competitionDesc {
	var comp_name string
	var comp_keyword string
	for div_desc := div.FirstChild; div_desc != nil; div_desc = div_desc.NextSibling {
		var class_name string
		for _, attr := range div_desc.Attr {
			if attr.Key == "class" {
				class_name = attr.Val
				break
			}
		}

		if class_name != "" {
			switch class_name {
			case "name ellipsis":
				comp_name = div_desc.FirstChild.Data
			case "info2 ellipsis keyword":
				comp_keyword = div_desc.FirstChild.FirstChild.Data
			}
		}
	}

	return &competitionDesc{comp_name, comp_keyword}
}

func main() {
	var c *colly.Collector = colly.NewCollector()

	// Find and visit all links
	// c.OnHTML("a[href]", func(e *colly.HTMLElement) {
	// 	e.Request.Visit(e.Attr("href"))
	// })

	// c.OnRequest(func(r *colly.Request) {
	// 	fmt.Println("Visiting", r.URL)
	// })

	// c.OnResponse(func(r *colly.Response) {
	// 	fmt.Println("visitied", r.Request.URL)
	// })

	c.OnHTML("div.competetion", func(e *colly.HTMLElement) { // not typo
		// desc := e.ChildText("div.desc p.name.ellipsis")
		var children *goquery.Selection = e.DOM.Children() // comp divs

		for _, s := range children.Nodes {
			var comp_info *html.Node = s.FirstChild.FirstChild

			for info_node := comp_info; info_node != nil; info_node = info_node.NextSibling {
				var class_name string

				for _, attr := range info_node.Attr {
					if attr.Key == "class" {
						class_name = attr.Val
						break
					}
				}

				if class_name != "" {
					switch class_name {
					case "pic":
						fmt.Println(extract_picinfo(info_node))
					case "desc":
						desc := extract_description(info_node)
						fmt.Println(desc.name, desc.keyword)
					case "etc":
						fmt.Println("etc")
					}
				}
			}
			fmt.Println("next competition")
		}

		// fmt.Printf("Child: %s\n", desc)
	})
	c.Visit("https://dacon.io/competitions")
}
