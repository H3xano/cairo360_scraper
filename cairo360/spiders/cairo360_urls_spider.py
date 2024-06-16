import scrapy
import os
import xml.etree.ElementTree as ET

class Cairo360URLSpider(scrapy.Spider):
    name = 'cairo360_urls'
    allowed_domains = ['cairo360.com']
    start_urls = ['https://www.cairo360.com/ar/sitemap.xml']
    url_list_filename = 'article_urls.txt'

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
        article_urls = [url.find('ns:loc', namespaces).text for url in root.findall('ns:url', namespaces)][1:]

        self.save_article_urls_to_file(article_urls)

    def save_article_urls_to_file(self, article_urls):
        with open(self.url_list_filename, 'a', encoding='utf-8') as file:
            for url in article_urls:
                file.write(f"{url}\n")
        self.logger.info(f"Saved {len(article_urls)} article URLs to {self.url_list_filename}")
