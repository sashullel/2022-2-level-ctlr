"""
Pipeline for CONLL-U formatting
"""
from pathlib import Path
from typing import List

from core_utils.article.article import (Article, get_article_id_from_filepath,
                                        SentenceProtocol, split_by_sentence)
from core_utils.article.io import from_raw, to_cleaned
from core_utils.article.ud import OpencorporaTagProtocol, TagConverter
from core_utils.constants import ASSETS_PATH

from string import punctuation

# pylint: disable=too-few-public-methods


class EmptyDirectoryError(Exception):
    """
    Directory is empty error
    """


class InconsistentDatasetError(Exception):
    """
    Inconsistency of files in the dataset directory error
    """


class CorpusManager:
    """
    Works with articles and stores them
    """
    def __init__(self, path_to_raw_txt_data: Path):
        """
        Initializes CorpusManager
        """
        self._storage = {}
        self._path_to_raw_txt_data = path_to_raw_txt_data
        self._validate_dataset()
        self._scan_dataset()

    def _validate_dataset(self) -> None:
        """
        Validates folder with assets
        """
        if not self._path_to_raw_txt_data.exists():
            raise FileNotFoundError('file does not exist')

        if not self._path_to_raw_txt_data.is_dir():
            raise NotADirectoryError('path does not lead to directory')

        meta_files = [file for file in self._path_to_raw_txt_data.glob('*.json')]
        raw_files = [file for file in self._path_to_raw_txt_data.glob('*.txt')]
        if not (meta_files and raw_files):
            raise EmptyDirectoryError('directory is empty')

        if len(meta_files) != len(raw_files):
            raise InconsistentDatasetError('the number of raw and meta files does not match')

        meta_files_idx = sorted(get_article_id_from_filepath(meta) for meta in meta_files)
        raw_files_idx = sorted(get_article_id_from_filepath(raw) for raw in raw_files)
        correct_range = [num for num in range(1, max(meta_files_idx) + 1)]
        if meta_files_idx != correct_range != raw_files_idx:
            raise InconsistentDatasetError('files are laid out in an inconsistent way')

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry
        """
        for file in self._path_to_raw_txt_data.glob('*.txt'):
            article = from_raw(file)
            self._storage.update({article.article_id: article})

    def get_articles(self) -> dict:
        """
        Returns storage params
        """
        return self._storage


class MorphologicalTokenDTO:
    """
    Stores morphological parameters for each token
    """

    def __init__(self, lemma: str = "", pos: str = "", tags: str = ""):
        """
        Initializes MorphologicalTokenDTO
        """


class ConlluToken:
    """
    Representation of the CONLL-U Token
    """

    def __init__(self, text: str):
        """
        Initializes ConlluToken
        """
        self._text = text

    def set_morphological_parameters(self, parameters: MorphologicalTokenDTO) -> None:
        """
        Stores the morphological parameters
        """

    def get_morphological_parameters(self) -> MorphologicalTokenDTO:
        """
        Returns morphological parameters from ConlluToken
        """

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        String representation of the token for conllu files
        """

    def get_cleaned(self) -> str:
        """
        Returns lowercase original form of a token
        """
        punc_to_remove = punctuation + '–—«»'
        return self._text.translate(self._text.maketrans('', '', punc_to_remove)).lower()


class ConlluSentence(SentenceProtocol):
    """
    Representation of a sentence in the CONLL-U format
    """

    def __init__(self, position: int, text: str, tokens: list[ConlluToken]):
        """
        Initializes ConlluSentence
        """
        self._position = position
        self._text = text
        self._tokens = tokens

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        Creates string representation of the sentence
        """

    def get_cleaned_sentence(self) -> str:
        """
        Returns the lowercase representation of the sentence
        """

    def get_tokens(self) -> list[ConlluToken]:
        """
        Returns sentences from ConlluSentence
        """
        return self._tokens


class MystemTagConverter(TagConverter):
    """
    Mystem Tag Converter
    """

    def convert_morphological_tags(self, tags: str) -> str:  # type: ignore
        """
        Converts the Mystem tags into the UD format
        """

    def convert_pos(self, tags: str) -> str:  # type: ignore
        """
        Extracts and converts the POS from the Mystem tags into the UD format
        """


class OpenCorporaTagConverter(TagConverter):
    """
    OpenCorpora Tag Converter
    """

    def convert_pos(self, tags: OpencorporaTagProtocol) -> str:  # type: ignore
        """
        Extracts and converts POS from the OpenCorpora tags into the UD format
        """

    def convert_morphological_tags(self, tags: OpencorporaTagProtocol) -> str:  # type: ignore
        """
        Converts the OpenCorpora tags into the UD format
        """


class MorphologicalAnalysisPipeline:
    """
    Preprocesses and morphologically annotates sentences into the CONLL-U format
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes MorphologicalAnalysisPipeline
        """
        self._corpus = corpus_manager

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Returns the text representation as the list of ConlluSentence
        """
        return [ConlluSentence(idx, sentence, []) for idx, sentence in enumerate(split_by_sentence(text))]

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """
        for key, val in self._corpus.get_articles():
            article = from_raw(val.get_raw_text_path(), val)
            article.set_conllu_sentences(self._process(article.get_raw_text()))
            to_cleaned(article)


class AdvancedMorphologicalAnalysisPipeline(MorphologicalAnalysisPipeline):
    """
    Preprocesses and morphologically annotates sentences into the CONLL-U format
    """

    def __init__(self, corpus_manager: CorpusManager):
        """
        Initializes MorphologicalAnalysisPipeline
        """
        self._corpus = corpus_manager

    def _process(self, text: str) -> List[ConlluSentence]:
        """
        Returns the text representation as the list of ConlluSentence
        """

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """


def main() -> None:
    """
    Entrypoint for pipeline module
    """
    corpus_manager = CorpusManager(ASSETS_PATH)
    storage = corpus_manager.get_articles()
    for idx, article in storage.items():
        pass


if __name__ == "__main__":
    main()
