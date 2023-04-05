"""
Crawler implementation
"""

from pathlib import Path
from typing import Pattern, Union

import re
import json
from bs4 import BeautifulSoup
import requests

from core_utils.config_dto import ConfigDTO
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH


class IncorrectSeedURLError(Exception):
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
        self._extract_config_content()

    def _extract_config_content(self) -> ConfigDTO:
        """
        Returns config values
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)

            config_dto = ConfigDTO(seed_urls=config_params['seed_urls'],
                                   headers=config_params['headers'],
                                   total_articles_to_find_and_parse=config_params['total_articles_to_find_and_parse'],
                                   encoding=config_params['encoding'],
                                   timeout=config_params['timeout'],
                                   should_verify_certificate=config_params['should_verify_certificate'],
                                   headless_mode=config_params['headless_mode']
                                   )
            return config_dto

    def _validate_config_content(self) -> None:
        """
        Ensure configuration parameters
        are not corrupt
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)

        seed_urls = config_params['seed_urls']
        total_articles = config_params['total_articles_to_find_and_parse']
        headers = config_params['headers']
        encoding = config_params['encoding']
        timeout = config_params['timeout']
        verify_cert = config_params['should_verify_certificate']

        if not all(re.match('https?://w?w?w?.', url) for url in seed_urls):
            raise IncorrectSeedURLError('seed URL does not match the standard pattern \
                                        or does not correspond to the target website')

        if total_articles not in range(1, 151):
            raise NumberOfArticlesOutOfRangeError('total number of articles is \
                                                  out of range from 1 to 150')

        if not isinstance(total_articles, int) or isinstance(total_articles, bool):
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')

        if not isinstance(headers, dict):
            raise IncorrectHeadersError('headers are not in a form of dictionary')

        if not isinstance(encoding, str):
            raise IncorrectEncodingError('encoding must be specified as a string')

        if timeout not in range(1, 60):
            raise IncorrectTimeoutError('timeout value must be a positive integer less than 60')

        if not isinstance(verify_cert, bool):
            raise IncorrectVerifyError('verify certificate value must either be True or False')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            seed_urls = json.load(f)['seed_urls']

        return list(str(url) for url in seed_urls)

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            total_articles = json.load(f)['total_articles_to_find_and_parse']

        return int(total_articles)

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            headers = json.load(f)['headers']

        pairs = [(str(key), str(val)) for key, val in headers.items()]
        return dict(pairs)

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            encoding = json.load(f)['encoding']

        return str(encoding)

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            timeout = json.load(f)['timeout']

        return int(timeout)

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            if_verify = json.load(f)['should_verify_certificate']

        return bool(if_verify)

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            if_headless = json.load(f)['headless_mode']

        return bool(if_headless)


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Delivers a response from a request
    with given configuration
    """
    response = requests.get(url, headers=config.get_headers(), timeout=config.get_timeout())
    if response.status_code == 200:
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
        pass

    def _extract_url(self, article_bs: BeautifulSoup) -> str:
        """
        Finds and retrieves URL from HTML
        """
        pass

    def find_articles(self) -> None:
        """
        Finds articles
        """
        pass

    def get_search_urls(self) -> list:
        """
        Returns seed_urls param
        """
        pass


class HTMLParser:
    """
    ArticleParser implementation
    """

    def __init__(self, full_url: str, article_id: int, config: Config) -> None:
        """
        Initializes an instance of the HTMLParser class
        """
        pass

    def _fill_article_with_text(self, article_soup: BeautifulSoup) -> None:
        """
        Finds text of article
        """
        pass

    def _fill_article_with_meta_information(self, article_soup: BeautifulSoup) -> None:
        """
        Finds meta information of article
        """
        pass

    def unify_date_format(self, date_str: str) -> datetime.datetime:
        """
        Unifies date format
        """
        pass

    def parse(self) -> Union[Article, bool, list]:
        """
        Parses each article
        """
        pass


def prepare_environment(base_path: Union[Path, str]) -> None:
    """
    Creates ASSETS_PATH folder if no created and removes existing folder
    """
    base_path.mkdir(exist_ok=True)


def main() -> None:
    """
    Entrypoint for scrapper module
    """
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)
    if configuration:
        prepare_environment(ASSETS_PATH)


if __name__ == "__main__":
    main()
