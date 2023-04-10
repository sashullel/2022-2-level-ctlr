"""
Crawler implementation
"""
import datetime
import json
import random
import re
import shutil
import time
from pathlib import Path
from typing import Pattern, Union

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from core_utils.article.article import Article
from core_utils.article.io import to_meta, to_raw
from core_utils.config_dto import ConfigDTO
from core_utils.constants import (ASSETS_PATH, CRAWLER_CONFIG_PATH,
                                  NUM_ARTICLES_UPPER_LIMIT,
                                  TIMEOUT_LOWER_LIMIT, TIMEOUT_UPPER_LIMIT)


class IncorrectSeedURLError(Exception):
    """"
    Seed URLs value is not of the list type or
    its elements either do not match the standard URL pattern
    or not of a string type
    """
    pass


class NumberOfArticlesOutOfRangeError(Exception):
    """
    The number of articles that must be parsed is out of given range
    """
    pass


class IncorrectNumberOfArticlesError(Exception):
    """
    The number of articles that must be parsed is not integer
    """
    pass


class IncorrectHeadersError(Exception):
    """
    Headers value is not of a dictionary type
    """
    pass


class IncorrectEncodingError(Exception):
    """
    Encoding value is not of a string type
    """
    pass


class IncorrectTimeoutError(Exception):
    """
    Timeout value is out of range from 1 to the given value
    """
    pass


class IncorrectVerifyError(Exception):
    """
    Should_verify_certificate value is not of a boolean type
    """
    pass


class Config:
    """
    Unpacks and validates configurations
    """

    seed_urls: list[str]
    num_articles: int
    headers: dict[str, str]
    encoding: str
    timeout: int
    verify_certificate: bool
    headless_mode: bool

    def __init__(self, path_to_config: Path) -> None:
        """
        Initializes an instance of the Config class
        """
        self.path_to_config = path_to_config
        self._validate_config_content()

        config_dto = self._extract_config_content()
        self._seed_urls = config_dto.seed_urls
        self._num_articles = config_dto.total_articles
        self._headers = config_dto.headers
        self._encoding = config_dto.encoding
        self._timeout = config_dto.timeout
        self._should_verify_certificate = config_dto.should_verify_certificate
        self._headless_mode = config_dto.headless_mode

    def _extract_config_content(self) -> ConfigDTO:
        """
        Returns config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return ConfigDTO(**config_params)

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters
        are not corrupt
        """
        config_dto = self._extract_config_content()

        if not isinstance(config_dto.seed_urls, list):
            raise IncorrectSeedURLError('seed URLs must be of passed as a list')

        if not all(re.match('https?://w?w?w?.*/', url) and isinstance(url, str) for url in config_dto.seed_urls):
            raise IncorrectSeedURLError('seed URLs either do not match the standard pattern '
                                        'or not strings')

        if not isinstance(config_dto.total_articles, int) or isinstance(config_dto.total_articles, bool) \
                or config_dto.total_articles < 1:
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')

        if config_dto.total_articles > NUM_ARTICLES_UPPER_LIMIT:
            raise NumberOfArticlesOutOfRangeError('total number of articles is '
                                                  'out of range from 1 to the given value')

        if not isinstance(config_dto.headers, dict):
            raise IncorrectHeadersError('headers are not in a form of a dictionary')

        if not isinstance(config_dto.encoding, str):
            raise IncorrectEncodingError('encoding must be specified as a string')

        if config_dto.timeout not in range(TIMEOUT_LOWER_LIMIT, TIMEOUT_UPPER_LIMIT + 1):
            raise IncorrectTimeoutError('timeout value must be a positive integer less than the given value')

        if not isinstance(config_dto.should_verify_certificate, bool) or \
                not isinstance(config_dto.headless_mode, bool):
            raise IncorrectVerifyError('verify certificate value must either be True or False')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls
        """
        return self._seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape
        """
        return self._num_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting
        """
        return self._headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing
        """
        return self._encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response
        """
        return self._timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate
        """
        return self._should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode
        """
        return self._headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Delivers a response from a request
    with given configuration
    """
    time.sleep(random.randint(1, 2))
    response = requests.get(url,
                            headers=config.get_headers(),
                            timeout=config.get_timeout(),
                            verify=config.get_verify_certificate())
    response.raise_for_status()
    return response


class Crawler:
    """
    Crawler implementation
    """

    url_pattern: Union[Pattern, str]

    def __init__(self, config: Config) -> None:
        """
        Initializes an instance of the Crawler class
        """
        self.config = config
        self.urls = []

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Finds and retrieves URL from HTML
        """
        links = article_bs.find_all('a')
        for link in links:
            url = link.get('href')
            if url and url.count('/') == 4 and url[:9] == '/novosti/':
                url = 'https://www.zebra-tv.ru' + url
                if url not in self.urls and len(self.urls) < self.config.get_num_articles():
                    self.urls.append(url)

    def find_articles(self) -> None:
        """
        Finds articles
        """
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        if self.config.get_headless_mode():
            chrome_options.add_argument('--headless=new')

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(self.config.get_seed_urls()[0])

        scroll_pause_time = 1.5
        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(self.urls) < self.config.get_num_articles():
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            current_html = driver.page_source
            bs = BeautifulSoup(current_html, 'lxml')
            self._extract_url(bs)

            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        driver.quit()

    def get_search_urls(self) -> list:
        """
        Returns seed_urls param
        """
        return self.config.get_seed_urls()


class HTMLParser:
    """
    ArticleParser implementation
    """

    def __init__(self, article_url: str, article_id: int, config: Config) -> None:
        """
        Initializes an instance of the HTMLParser class
        """
        self.article_url = article_url
        self.article_id = article_id
        self.config = config
        self.article = Article(url=self.article_url, article_id=self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Finds text of article
        """
        # get the title
        title = article_soup.find_all('h1', {'class': 'new-title'})[0]
        title_text = title.text

        # get the preview
        preview = article_soup.find_all('div', {'class': 'preview-text'})[0]
        preview_text = preview.text.strip()
        if preview_text[-1] not in '.?!':
            preview_text += '.'

        # get the article body
        body_bs = article_soup.find_all('div', {'class': 'detail'})[0]
        paragraph_texts = [par.text.strip() for par in body_bs.find_all('p')]
        article_text = ' '.join(paragraph_texts)

        self.article.title = title_text
        self.article.text = preview_text + ' ' + article_text

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Finds meta information of article
        """
        try:
            author = article_soup.find_all('span', {'class': 'author'})
            self.article.author.extend(author[0].text[7:].split(', '))
        except IndexError:
            self.article.author.append('NOT FOUND')

        article_date = article_soup.find(itemprop='datePublished').get('content')
        article_time = article_soup.find_all('span', {'class': 'date'})[0].text[-6:]
        date_n_time = self.unify_date_format(article_date + article_time)
        self.article.date = date_n_time

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unifies date format
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parses each article
        """
        response = make_request(self.article_url, self.config)
        article_bs = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)
        return self.article


def prepare_environment(base_path: Union[Path, str]) -> None:
    """
    Creates ASSETS_PATH folder if no created and removes existing folder
    """
    try:
        base_path.mkdir(parents=True)
    except FileExistsError:
        shutil.rmtree(base_path)
        base_path.mkdir(parents=True)


def main() -> None:
    """
    Entrypoint for scrapper module
    """
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(config=configuration)
    crawler.find_articles()
    search_urls = crawler.urls()
    print(search_urls)

    for id, url in enumerate(search_urls, start=1):
        parser = HTMLParser(article_url=search_urls[id], article_id=id, config=configuration)
        parsed_article = parser.parse()
        to_raw(parsed_article)
        to_meta(parsed_article)
        print(id)


if __name__ == "__main__":
    main()
