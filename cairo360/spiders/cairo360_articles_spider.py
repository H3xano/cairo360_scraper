import scrapy
import os
import json
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider

class Cairo360ArticleSpider(scrapy.Spider):
    name = 'cairo360_articles'
    allowed_domains = ['cairo360.com']
    url_list_filename = 'article_urls.txt'
    articles_directory = 'articles'
    progress_filename = 'progress.json'
    failed_tasks_filename = 'failed_tasks.txt'
    combined_output_filename = 'combined_articles.json'

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
        """
        Start the scraping process by loading the list of article URLs and initiating requests.
        """
        if not os.path.exists(self.url_list_filename):
            self.logger.error(f"URL list file {self.url_list_filename} not found")
            raise CloseSpider(f"URL list file {self.url_list_filename} not found")

        article_urls = self.load_article_urls_from_file()
        processed_urls = self.load_processed_urls()

        for index, url in enumerate(article_urls):
            if url not in processed_urls:
                yield scrapy.Request(url=url, callback=self.parse_article, errback=self.errback_article,
                                     meta={'index': index, 'url': url})

    def parse_article(self, response):
        """
        Parse the article page to extract the title and content.
        """
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
            self.save_failed_task(url, str(e))

    def errback_article(self, failure):
        """
        Handle errors during requests.
        """
        url = failure.request.url
        self.logger.error(f"Request failed: {url}")
        self.logger.error(repr(failure))
        self.save_failed_task(url, repr(failure))

    def save_article_to_json(self, article, index):
        """
        Save the extracted article data to a JSON file.
        """
        try:
            if not os.path.exists(self.articles_directory):
                os.makedirs(self.articles_directory)
            filename = os.path.join(self.articles_directory, f"{index}.json")
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(article, file, ensure_ascii=False, indent=4)
            self.logger.info(f"Saved article {index} to {filename}")
        except IOError as e:
            self.logger.error(f"Error saving article to {filename}: {e}")

    def save_progress(self, url):
        """
        Save the URL of the processed article to the progress file.
        """
        processed_urls = self.load_processed_urls()
        processed_urls.add(url)
        try:
            with open(self.progress_filename, 'w', encoding='utf-8') as file:
                json.dump(list(processed_urls), file, ensure_ascii=False, indent=4)
        except IOError as e:
            self.logger.error(f"Error saving progress to {self.progress_filename}: {e}")

    def load_processed_urls(self):
        """
        Load the URLs of already processed articles from the progress file.
        """
        if os.path.exists(self.progress_filename):
            try:
                with open(self.progress_filename, 'r', encoding='utf-8') as file:
                    return set(json.load(file))
            except IOError as e:
                self.logger.error(f"Error loading progress from {self.progress_filename}: {e}")
                return set()
        return set()

    def load_article_urls_from_file(self):
        """
        Load the list of article URLs from the file.
        """
        try:
            with open(self.url_list_filename, 'r', encoding='utf-8') as file:
                return [line.strip() for line in file.readlines()]
        except IOError as e:
            self.logger.error(f"Error loading article URLs from {self.url_list_filename}: {e}")
            return []

    def save_failed_task(self, url, error_message):
        """
        Save the URL and error message of failed tasks to a file.
        """
        try:
            with open(self.failed_tasks_filename, 'a', encoding='utf-8') as file:
                file.write(f"{error_message}: {url}\n")
            self.logger.info(f"Saved failed task: {url} with error {error_message}")
        except IOError as e:
            self.logger.error(f"Error saving failed task to {self.failed_tasks_filename}: {e}")

    def closed(self, reason):
        """
        Called when the spider is closed. Combines all article JSON files into a single JSON file.
        """
        try:
            self.combine_json_files(self.articles_directory, self.combined_output_filename)
            self.logger.info(f"Combined all articles into {self.combined_output_filename}")
        except Exception as e:
            self.logger.error(f"Error combining JSON files: {e}")

    def combine_json_files(self, input_directory, output_file):
        """
        Combine individual article JSON files into a single JSON file.
        """
        json_list = []

        try:
            for filename in os.listdir(input_directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(input_directory, filename)
                    with open(file_path, 'r', encoding='utf-8') as file:
                        json_content = json.load(file)
                        json_list.append(json_content)

            with open(output_file, 'w', encoding='utf-8') as output:
                json.dump(json_list, output, ensure_ascii=False, indent=4)
        except IOError as e:
            self.logger.error(f"Error combining JSON files: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON file: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
