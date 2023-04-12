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
    or not of the string type
    """


class NumberOfArticlesOutOfRangeError(Exception):
    """
    The number of articles that must be parsed is out of given range
    """


class IncorrectNumberOfArticlesError(Exception):
    """
    The number of articles that must be parsed is not integer
    """


class IncorrectHeadersError(Exception):
    """
    Headers value is not of the dictionary type
    """


class IncorrectEncodingError(Exception):
    """
    Encoding value is not of a string type
    """


class IncorrectTimeoutError(Exception):
    """
    Timeout value is out of range from 1 to the given value
    """


class IncorrectVerifyError(Exception):
    """
    Should_verify_certificate value is not of a boolean type
    """


class Config:
    """
    Unpacks and validates configurations
    """
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

        if not all(re.match('^https?://[w{3}]?.*/', url) and
                   isinstance(url, str) for url in config_dto.seed_urls):
            raise IncorrectSeedURLError('seed URLs either do not match the standard pattern '
                                        'or not strings')

        if not isinstance(config_dto.total_articles, int) or \
                isinstance(config_dto.total_articles, bool) \
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
            raise IncorrectTimeoutError('timeout value must be a positive integer '
                                        'less than the given value')

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
    time.sleep(random.randint(2, 4))
    response = requests.get(url,
                            headers=config.get_headers(),
                            timeout=config.get_timeout(),
                            verify=config.get_verify_certificate())
    response.raise_for_status()
    response.encoding = config.get_encoding()
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
        url = article_bs.get('href')
        if url and url.count('/') == 4 and url.startswith('/novosti/'):
            return 'https://www.zebra-tv.ru' + str(url)
        return ''

    def find_articles(self) -> None:
        """
        Finds articles
        """
        for seed_url in self.config.get_seed_urls():
            try:
                response = make_request(seed_url, self.config)

            except requests.exceptions.HTTPError:
                continue

            links = BeautifulSoup(response.text, 'lxml').find_all('a')
            for link in links:
                if len(self.urls) < self.config.get_num_articles():
                    url = self._extract_url(link)
                    if url:
                        self.urls.append(url)

    def get_search_urls(self) -> list:
        """
        Returns seed_urls param
        """
        return self.config.get_seed_urls()


class HTMLParser:
    """
    ArticleParser implementation
    """

    def __init__(self, full_url: str, article_id: int, config: Config) -> None:
        """
        Initializes an instance of the HTMLParser class
        """
        self.full_url = full_url
        self.article_id = article_id
        self.config = config
        self.article = Article(url=self.full_url, article_id=self.article_id)

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Finds text of article
        """
        title = article_soup.find('h1', {'class': 'new-title'})
        self.article.title = title.text

        preview = article_soup.find('div', {'class': 'preview-text'})
        body_bs = article_soup.find('div', {'class': 'detail'})
        paragraphs = ' '.join([par.text.strip() for par in body_bs.find_all('p')])

        self.article.text = f'{preview.text.strip()}. {paragraphs}'

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Finds meta information of article
        """
        author = article_soup.find('span', itemprop='author')
        if author:
            self.article.author.extend(author.text.split(', '))
        else:
            self.article.author.append('NOT FOUND')

        article_date = article_soup.find('meta', itemprop='datePublished').get('content')
        article_time = article_soup.find('span', {'class': 'date'}).text[-6:]
        if article_date and article_time:
            self.article.date = self.unify_date_format(str(article_date) + article_time)

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unifies date format
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')

    def parse(self) -> Union[Article, bool, list]:
        """
        Parses each article
        """
        response = make_request(self.full_url, self.config)
        article_bs = BeautifulSoup(response.text, 'lxml')
        self._fill_article_with_text(article_bs)
        self._fill_article_with_meta_information(article_bs)
        return self.article


def prepare_environment(base_path: Union[Path, str]) -> None:
    """
    Creates ASSETS_PATH folder if no created and removes existing folder
    """
    if base_path.exists():
        shutil.rmtree(base_path)
    base_path.mkdir(parents=True)


class CrawlerRecursive(Crawler):
    """
    Recursive crawler implementation
    """
    def __init__(self, config: Config):
        super().__init__(config)
        self.crawler_data_path = Path(__file__).parent / 'crawler_data.json'
        self.start_url = config.get_seed_urls()[0]
        self.load_crawler_data()

    def save_crawler_data(self) -> None:
        """
        Saves start_url and collected urls
        from crawler into a json file
        """
        crawler_data = {'start_url': self.start_url, 'urls': self.urls}

        with open(self.crawler_data_path, 'w', encoding='utf-8') as f:
            json.dump(crawler_data, f, ensure_ascii=True, indent=4, separators=(', ', ': '))

    def load_crawler_data(self) -> None:
        """
        Loads start_url and collected urls
        from a json file into crawler
        """
        if self.crawler_data_path.exists():
            with open(self.crawler_data_path, 'r', encoding='utf-8') as f:
                crawler_data = json.load(f)
            self.start_url = crawler_data['start_url']
            self.urls = crawler_data['urls']

    def find_articles(self) -> None:
        """
        Finds articles
        """
        try:
            response = make_request(self.start_url, self.config)
        except requests.exceptions.HTTPError:
            pass

        else:
            links = BeautifulSoup(response.text, 'lxml').find_all('a')
            for link in links:
                if len(self.urls) < self.config.get_num_articles():
                    url = self._extract_url(link)
                    if url and url not in self.urls:
                        self.urls.append(url)
                        self.start_url = url
                        self.save_crawler_data()

        while len(self.urls) < self.config.get_num_articles():
            self.find_articles()


def main() -> None:
    """
    Entrypoint for scrapper module
    """
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    crawler = Crawler(config=configuration)
    crawler.find_articles()

    for idx, url in enumerate(crawler.urls, start=1):
        parser = HTMLParser(full_url=url, article_id=idx, config=configuration)
        parsed_article = parser.parse()
        if isinstance(parsed_article, Article):
            to_raw(parsed_article)
            to_meta(parsed_article)


def main_recursive() -> None:
    """
    Entrypoint for scrapper module using recursive crawler
    """
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
    prepare_environment(ASSETS_PATH)
    recursive_crawler = CrawlerRecursive(config=configuration)
    recursive_crawler.find_articles()

    for idx, url in enumerate(recursive_crawler.urls, start=1):
        parser = HTMLParser(full_url=url, article_id=idx, config=configuration)
        parsed_article = parser.parse()
        if isinstance(parsed_article, Article):
            to_raw(parsed_article)
            to_meta(parsed_article)


if __name__ == "__main__":
    main()
