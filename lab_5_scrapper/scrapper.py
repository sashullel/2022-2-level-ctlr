"""
Crawler implementation
"""
import shutil
from pathlib import Path
from typing import Pattern, Union

import re
import json
from bs4 import BeautifulSoup
import requests
import datetime
from selenium import webdriver
from requests import HTTPError
from selenium.webdriver.chrome.options import Options as ChromeOptions
import time

from core_utils.article.article import Article
from core_utils.article.io import to_raw, to_meta
# from core_utils.article.ud import
from core_utils.config_dto import ConfigDTO
from core_utils.constants import (ASSETS_PATH, CRAWLER_CONFIG_PATH,
                                  NUM_ARTICLES_UPPER_LIMIT, TIMEOUT_LOWER_LIMIT,
                                  TIMEOUT_UPPER_LIMIT)


class IncorrectSeedURLError(Exception):
    '''

    '''
    pass


class NumberOfArticlesOutOfRangeError(Exception):
    pass


class IncorrectNumberOfArticlesError(Exception):
    pass


class IncorrectHeadersError(Exception):
    pass


class IncorrectEncodingError(Exception):
    pass


class IncorrectTimeoutError(Exception):
    pass


class IncorrectVerifyError(Exception):
    pass


class Config:
    """
    Unpacks and validates configurations
    """

    seed_urls: list[str]
    total_articles_to_find_and_parse: int
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

    def _extract_config_content(self) -> ConfigDTO:
        """
        Returns config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)

            self.config_dto = ConfigDTO(seed_urls=config_params['seed_urls'],
                                        headers=config_params['headers'],
                                        total_articles_to_find_and_parse=
                                        config_params['total_articles_to_find_and_parse'],
                                        encoding=config_params['encoding'],
                                        timeout=config_params['timeout'],
                                        should_verify_certificate=
                                        config_params['should_verify_certificate'],
                                        headless_mode=config_params['headless_mode'])

            return self.config_dto

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters
        are not corrupt
        """
        config_dto = self._extract_config_content()

        if not all(re.match('https?://w?w?w?.', url) for url in config_dto.seed_urls):
            raise IncorrectSeedURLError('seed URL does not match the standard pattern')

        if config_dto.total_articles not in range(1, NUM_ARTICLES_UPPER_LIMIT):
            raise NumberOfArticlesOutOfRangeError('total number of articles is '
                                                  'out of the given range')

        if not isinstance(config_dto.total_articles, int) or isinstance(config_dto.total_articles, bool):
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')

        if not isinstance(config_dto.headers, dict):
            raise IncorrectHeadersError('headers are not in a form of a dictionary')

        if not isinstance(config_dto.encoding, str):
            raise IncorrectEncodingError('encoding must be specified as a string')

        if config_dto.timeout not in range(TIMEOUT_LOWER_LIMIT, TIMEOUT_UPPER_LIMIT + 1):
            raise IncorrectTimeoutError('timeout value must be a positive integer less than the given value')

        if not isinstance(config_dto.should_verify_certificate, bool):
            raise IncorrectVerifyError('verify certificate value must either be True or False')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls
        """
        return self.config_dto.seed_urls

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape
        """
        return self.config_dto.total_articles

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting
        """
        return self.config_dto.headers

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing
        """
        return self.config_dto.encoding

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response
        """
        return self.config_dto.timeout

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate
        """
        return self.config_dto.should_verify_certificate

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode
        """
        return self.config_dto.headless_mode


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Delivers a response from a request
    with given configuration
    """
    response = requests.get(url, headers=config.get_headers(),
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
            url = link['href']
            if url.count('/') == 4 and url[:9] == '/novosti/':
                url = 'https://www.zebra-tv.ru' + url
                if url not in self.urls and len(self.urls) < self.config.get_num_articles():
                    self.urls.append(url)
                    print(url)

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

        scroll_pause_time = 2.5
        last_height = driver.execute_script("return document.body.scrollHeight")
        while len(self.urls) != self.config.get_num_articles():
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")

            current_html = driver.page_source
            bs = BeautifulSoup(current_html, 'lxml')
            self._extract_url(bs)

            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def get_search_urls(self) -> list:
        """
        Returns seed_urls param
        """
        return self.urls


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
            self.article.author = author[0].text[7:].strip(', ')
        except IndexError:
            self.article.author = ['NOT FOUND']

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


def main() -> None:
    """
    Entrypoint for scrapper module
    """
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(config=configuration)
    crawler.find_articles()
    search_urls = crawler.get_search_urls()
    print(search_urls)
    for i in range(1, len(search_urls) + 1):
        parser = HTMLParser(article_url=search_urls[i - 1], article_id=i, config=configuration)
        parsed_article = parser.parse()
        to_raw(parsed_article)
        to_meta(parsed_article)
        print(i)


if __name__ == "__main__":
    main()
