import scrapy
import os
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


class Cairo360URLSpider(scrapy.Spider):
    name = 'cairo360_urls'
    allowed_domains = ['cairo360.com']
    start_urls = ['https://www.cairo360.com/ar/sitemap.xml']
    url_list_filename = 'article_urls.txt'
    discarded_urls_filename = 'discarded_urls.txt'

    def __init__(self, *args, **kwargs):
        super(Cairo360URLSpider, self).__init__(*args, **kwargs)
        self.existing_urls = self.load_existing_urls()

    def load_existing_urls(self):
        """
        Load existing URLs from the file to avoid duplication.
        """
        if os.path.exists(self.url_list_filename):
            with open(self.url_list_filename, 'r', encoding='utf-8') as file:
                return set(line.strip() for line in file)
        return set()

    def parse(self, response):
        """
        Parse the main sitemap and extract article sitemap URLs.
        """
        try:
            sitemap_content = response.body
            root = ET.fromstring(sitemap_content)
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            article_sitemaps = [
                sitemap.find('ns:loc', namespaces).text
                for sitemap in root.findall('ns:sitemap', namespaces)
                if 'article-sitemap' in sitemap.find('ns:loc', namespaces).text
            ]

            for sitemap in article_sitemaps:
                yield scrapy.Request(url=sitemap, callback=self.parse_article_sitemap)

        except ET.ParseError as e:
            self.logger.error(f"Error parsing sitemap XML: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def parse_article_sitemap(self, response):
        """
        Parse each article sitemap and extract article URLs.
        """
        try:
            sitemap_content = response.body
            root = ET.fromstring(sitemap_content)
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            article_urls = [
                               url.find('ns:loc', namespaces).text
                               for url in root.findall('ns:url', namespaces)
                           ][1:]  # Skip the first URL if necessary

            valid_article_urls = []
            for url in article_urls:
                if url is None:
                    self.save_discarded_url("None", url)
                elif not self.is_valid_url(url):
                    self.save_discarded_url("Invalid", url)
                elif url in self.existing_urls:
                    self.save_discarded_url("Duplicate", url)
                else:
                    valid_article_urls.append(url)

            self.save_article_urls_to_file(valid_article_urls)

        except ET.ParseError as e:
            self.logger.error(f"Error parsing article sitemap XML: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def is_valid_url(self, url):
        """
        Validate the URL format.
        """
        if url is None:
            return False
        parsed_url = urlparse(url)
        return bool(parsed_url.scheme) and bool(parsed_url.netloc)

    def save_article_urls_to_file(self, article_urls):
        """
        Save the extracted article URLs to a file.
        """
        try:
            with open(self.url_list_filename, 'a', encoding='utf-8') as file:
                for url in article_urls:
                    file.write(f"{url}\n")
            self.logger.info(f"Saved {len(article_urls)} new article URLs to {self.url_list_filename}")
            self.existing_urls.update(article_urls)

        except IOError as e:
            self.logger.error(f"Error writing to file {self.url_list_filename}: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")

    def save_discarded_url(self, reason, url):
        """
        Save discarded URL with the reason to a file.
        """
        try:
            with open(self.discarded_urls_filename, 'a', encoding='utf-8') as file:
                file.write(f"{reason}: {url}\n")
            self.logger.info(f"Discarded URL ({reason}): {url}")

        except IOError as e:
            self.logger.error(f"Error writing to file {self.discarded_urls_filename}: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
