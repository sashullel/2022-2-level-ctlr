"""
Crawler implementation
"""
from bs4 import BeautifulSoup
from core_utils.constants import ASSETS_PATH, CRAWLER_CONFIG_PATH
from core_utils.config_dto import ConfigDTO
from pathlib import Path
from typing import Pattern, Union
import json
import re
import requests


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
        if not all(re.match('https?://w?w?w?.', link) for link in self.get_seed_urls()):
            raise IncorrectSeedURLError('seed URL does not match standard pattern "https?://w?w?w?." \
                                            or does not correspond to the target website')

        if self.get_num_articles() not in range(1, 151):
            raise NumberOfArticlesOutOfRangeError('total number of articles is out of range from 1 to 150')

        if not isinstance(self.get_num_articles(), int) or isinstance(self.get_num_articles(), bool):
            raise IncorrectNumberOfArticlesError('total number of articles to parse is not integer')

        if not isinstance(self.get_headers(), dict):
            raise IncorrectHeadersError('headers are not in a form of dictionary')

        if not isinstance(self.get_encoding(), str):
            raise IncorrectEncodingError('encoding must be specified as a string')

        if not self.get_timeout() in range(1, 60):
            raise IncorrectTimeoutError('timeout value must be a positive integer less than 60')

        if not isinstance(self.get_verify_certificate(), bool):
            raise IncorrectVerifyError('verify certificate value must either be True or False')

    def get_seed_urls(self) -> list[str]:
        """
        Retrieve seed urls
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['seed_urls']

    def get_num_articles(self) -> int:
        """
        Retrieve total number of articles to scrape
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['total_articles_to_find_and_parse']

    def get_headers(self) -> dict[str, str]:
        """
        Retrieve headers to use during requesting
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['headers']

    def get_encoding(self) -> str:
        """
        Retrieve encoding to use during parsing
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['encoding']

    def get_timeout(self) -> int:
        """
        Retrieve number of seconds to wait for response
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['timeout']

    def get_verify_certificate(self) -> bool:
        """
        Retrieve whether to verify certificate
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['should_verify_certificate']

    def get_headless_mode(self) -> bool:
        """
        Retrieve whether to use headless mode
        """
        with open(self.path_to_config, 'r', encoding='utf-8') as f:
            config_params = json.load(f)
        return config_params['headless_mode']


def make_request(url: str, config: Config) -> requests.models.Response:
    """
    Delivers a response from a request
    with given configuration
    """
    pass


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
    ASSETS_PATH.mkdir(exist_ok=True)



def main() -> None:
    """
    Entrypoint for scrapper module
    """
    configuration = Config(path_to_config=CRAWLER_CONFIG_PATH)


if __name__ == "__main__":
    main()
