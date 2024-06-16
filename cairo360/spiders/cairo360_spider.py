import scrapy
import os
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

class Cairo360Spider(scrapy.Spider):
    name = 'cairo360'
    allowed_domains = ['cairo360.com']
    start_urls = ['https://www.cairo360.com/ar/sitemap.xml']
    url_list_filename = 'article_urls.txt'
    progress_filename = 'progress.json'
    articles_directory = 'articles'
    article_count = 0  # Counter to keep track of the number of articles processed
    article_limit = 10  # Limit to the number of articles to process

    def start_requests(self):
        # Check if the article URL list file exists
        if os.path.exists(self.url_list_filename):
            self.logger.info(f"Loading article URLs from {self.url_list_filename}")
            article_urls = self.load_article_urls_from_file()
            self.logger.info(f"Found {len(article_urls)} article URLs")
            for url in article_urls:
                yield scrapy.Request(url=url, callback=self.parse_article, errback=self.errback_article)
        else:
            self.logger.info(f"Fetching sitemap from {self.start_urls[0]}")
            yield scrapy.Request(url=self.start_urls[0], callback=self.parse)

    def parse(self, response):
        sitemap_content = response.body
        root = ET.fromstring(sitemap_content)
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        article_sitemaps = [sitemap.find('ns:loc', namespaces).text for sitemap in
                            root.findall('ns:sitemap', namespaces) if
                            'article-sitemap' in sitemap.find('ns:loc', namespaces).text]

        for sitemap in article_sitemaps:
            yield scrapy.Request(url=sitemap, callback=self.parse_article_sitemap)

    def parse_article_sitemap(self, response):
        sitemap_content = response.body
        root = ET.fromstring(sitemap_content)
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        article_urls = [url.find('ns:loc', namespaces).text for url in root.findall('ns:url', namespaces)]

        self.save_article_urls_to_file(article_urls)

        for url in article_urls:
            if url is None:
                self.logger.warning("Found None URL in article_sitemap")
                continue

            self.logger.info(f"Processing URL: {url}")
            yield scrapy.Request(url=url, callback=self.parse_article, errback=self.errback_article)

    def parse_article(self, response):
        if self.article_count >= self.article_limit:
            return

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.select_one('h2.media-heading').text.strip()
            self.logger.info(f"Parsing article {title}")
            content = soup.select_one('.article-inner-content').get_text(strip=True)
            self.logger.info(f"Parsing content {content}")
            if not title or not content:
                raise ValueError("Title or content missing")

            article_data = {
                'url': response.url,
                'title': title,
                'content': content
            }
            self.save_article_to_json(article_data, self.article_count)
            self.article_count += 1
            self.logger.info(f"Processed {self.article_count} articles: {response.url}")
            yield article_data
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")
            # self.logger.error(f"Response text: {response.text}")

    def errback_article(self, failure):
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(repr(failure))

    def save_article_urls_to_file(self, article_urls):
        with open(self.url_list_filename, 'w', encoding='utf-8') as file:
            for url in article_urls:
                file.write(f"{url}\n")

    def save_article_to_json(self, article, index):
        if not os.path.exists(self.articles_directory):
            os.makedirs(self.articles_directory)
        filename = os.path.join(self.articles_directory, f"{index}.json")
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(article, file, ensure_ascii=False, indent=4)
        self.logger.info(f"Saved article {index} to {filename}")

    def load_article_urls_from_file(self):
        if os.path.exists(self.url_list_filename):
            with open(self.url_list_filename, 'r', encoding='utf-8') as file:
                return [line.strip() for line in file.readlines()]
        else:
            return []
