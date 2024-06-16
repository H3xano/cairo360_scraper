# Cairo360 Scraper

This project consists of two Scrapy spiders designed to scrape article URLs and their contents from the Cairo360 website. The first spider, `Cairo360URLSpider`, extracts article URLs from the sitemap. The second spider, `Cairo360ArticleSpider`, scrapes the article contents based on the extracted URLs.

## Project Structure

- `cairo360_urls_spider.py`: Scrapy spider to extract article URLs from the sitemap.
- `cairo360_articles_spider.py`: Scrapy spider to scrape article contents from the extracted URLs.
- `articles/`: Directory where individual article JSON files are saved.
- `article_urls.txt`: File containing the list of extracted article URLs.
- `progress.json`: File to keep track of processed URLs for resuming interrupted scraping sessions.
- `failed_tasks.txt`: File to log URLs that failed to be processed along with the error messages.
- `combined_articles.json`: File containing all the combined article data.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/H3xano/cairo360_scraper.git
    cd cairo360_scraper
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Running the Spiders

1. **Extract Article URLs:**

    Run the `Cairo360URLSpider` to extract article URLs from the sitemap:
    ```sh
    scrapy crawl cairo360_urls
    ```

    This will generate a file named `article_urls.txt` containing the extracted URLs.

2. **Scrape Articles:**

    Run the `Cairo360ArticleSpider` to scrape the article contents from the extracted URLs:
    ```sh
    scrapy crawl cairo360_articles
    ```

    This will create individual JSON files for each article in the `articles/` directory, keep track of the processed URLs in `progress.json`, and log any failed tasks in `failed_tasks.txt`.

### Combining JSON Files

After the `Cairo360ArticleSpider` completes, it will automatically combine all individual article JSON files into a single file named `combined_articles.json`.

## Error Handling

- **Invalid or Duplicate URLs:** The `Cairo360URLSpider` ensures that only valid, non-duplicate URLs are saved to `article_urls.txt`. Invalid or duplicate URLs are logged in `discarded_urls.txt`.
- **Failed Tasks:** The `Cairo360ArticleSpider` logs any URLs that fail to be processed, along with the error messages, in `failed_tasks.txt`.

## Notes

- Ensure that the `articles/` directory and the files `article_urls.txt`, `progress.json`, and `failed_tasks.txt` exist in the working directory.
- The spider is designed to handle interruptions and resume from where it left off using the `progress.json` file.
- Custom headers are used to mimic a real browser and avoid potential blocking by the website.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes or improvements.

## Contact

For questions or suggestions, please contact me.
