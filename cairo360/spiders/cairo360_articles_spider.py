import scrapy
import os
import json
from bs4 import BeautifulSoup


class Cairo360ArticleSpider(scrapy.Spider):
    name = 'cairo360_articles'
    allowed_domains = ['cairo360.com']
    url_list_filename = 'article_urls.txt'
    articles_directory = 'articles'
    progress_filename = 'progress.json'

    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Host': 'www.cairo360.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Cookie': 'PHPSESSID=akmc9jug8gnmc734igbqe41h78; wp-wpml_current_language=ar',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'DNT': '1',
            'Sec-GPC': '1',
            'Priority': 'u=1',
        }
    }

    def start_requests(self):
        if not os.path.exists(self.url_list_filename):
            self.logger.error(f"URL list file {self.url_list_filename} not found")
            return

        article_urls = self.load_article_urls_from_file()
        processed_urls = self.load_processed_urls()

        for index, url in enumerate(article_urls):
            if url not in processed_urls:
                yield scrapy.Request(url=url, callback=self.parse_article, errback=self.errback_article,
                                     meta={'index': index, 'url': url})

    def parse_article(self, response):
        index = response.meta['index']
        url = response.meta['url']
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.select_one('h2.media-heading').text.strip()
            content = soup.select_one('.article-inner-content').get_text(strip=True)

            if not title or not content:
                raise ValueError("Title or content missing")

            article_data = {
                'url': response.url,
                'title': title,
                'content': content
            }
            self.save_article_to_json(article_data, index)
            self.save_progress(url)
            self.logger.info(f"Processed article: {response.url}")
            yield article_data
        except Exception as e:
            self.logger.error(f"Error processing {response.url}: {e}")

    def errback_article(self, failure):
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(repr(failure))

    def save_article_to_json(self, article, index):
        if not os.path.exists(self.articles_directory):
            os.makedirs(self.articles_directory)
        filename = os.path.join(self.articles_directory, f"{index}.json")
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(article, file, ensure_ascii=False, indent=4)
        self.logger.info(f"Saved article {index} to {filename}")

    def save_progress(self, url):
        processed_urls = self.load_processed_urls()
        processed_urls.add(url)
        with open(self.progress_filename, 'w', encoding='utf-8') as file:
            json.dump(list(processed_urls), file, ensure_ascii=False, indent=4)

    def load_processed_urls(self):
        if os.path.exists(self.progress_filename):
            with open(self.progress_filename, 'r', encoding='utf-8') as file:
                return set(json.load(file))
        return set()

    def load_article_urls_from_file(self):
        with open(self.url_list_filename, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
