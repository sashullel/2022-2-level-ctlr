"""
Pipeline for CONLL-U formatting
"""
import string
from pathlib import Path
from typing import List

from pymystem3 import Mystem

from core_utils.article.article import (Article, get_article_id_from_filepath,
                                        SentenceProtocol, split_by_sentence)
from core_utils.article.io import from_raw, to_conllu, to_cleaned
from core_utils.article.ud import OpencorporaTagProtocol, TagConverter
from core_utils.constants import ASSETS_PATH

import re

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

        meta_files = [file for file in self._path_to_raw_txt_data.glob('*_meta.json')]
        raw_files = [file for file in self._path_to_raw_txt_data.glob('*_raw.txt')]
        if not (meta_files and raw_files):
            raise EmptyDirectoryError('directory is empty')

        if len(meta_files) != len(raw_files):
            raise InconsistentDatasetError('the number of raw and meta files does not match')

        meta_files_idx = sorted(get_article_id_from_filepath(meta) for meta in meta_files)
        raw_files_idx = sorted(get_article_id_from_filepath(raw) for raw in raw_files)
        correct_range = [num for num in range(1, max(meta_files_idx) + 1)]
        if meta_files_idx != correct_range != raw_files_idx:
            raise InconsistentDatasetError('files are laid out in an inconsistent way')

        for file in meta_files + raw_files:
            with open(file, 'r', encoding='utf-8') as f:
                if not f.read():
                    raise InconsistentDatasetError('there is an empty file')

    def _scan_dataset(self) -> None:
        """
        Register each dataset entry
        """
        for file_path in self._path_to_raw_txt_data.glob('*_raw.txt'):
            article = from_raw(file_path)
            self._storage[article.article_id] = article

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
        self.lemma = lemma
        self.pos = pos
        self.tags = tags


class ConlluToken:
    """
    Representation of the CONLL-U Token
    """

    def __init__(self, text: str):
        """
        Initializes ConlluToken
        """
        self._text = text
        self._morphological_parameters = MorphologicalTokenDTO()
        self._position = 0

    def set_morphological_parameters(self, parameters: MorphologicalTokenDTO) -> None:
        """
        Stores the morphological parameters
        """
        self._morphological_parameters = parameters

    def get_morphological_parameters(self) -> MorphologicalTokenDTO:
        """
        Returns morphological parameters from ConlluToken
        """
        return self._morphological_parameters

    def set_position(self, position: int) -> None:
        """
        Stores the morphological parameters
        """
        self._position = position

    def get_position(self) -> int:
        """
        Returns morphological parameters from ConlluToken
        """
        return self._position

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        String representation of the token for conllu files
        """
        position = str(self._position)
        xpos = '_'
        feats = tags if include_morphological_tags and (tags := self._morphological_parameters.tags) else '_'
        head = '0'
        deprel = 'root'
        deps = '_'
        misc = '_'

        return '\t'.join((position, self._text, self._morphological_parameters.lemma,
                          self._morphological_parameters.pos, xpos, feats, head, deprel, deps, misc))

    def get_cleaned(self) -> str:
        """
        Returns lowercase original form of a token
        """
        return re.sub(r'[^\w\s]', '', self._text).lower()


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

    def _format_tokens(self, include_morphological_tags: bool) -> str:
        """
        Formats tokens per newline
        """
        if include_morphological_tags:
            return '\n'.join((token.get_conllu_text(include_morphological_tags) for token in self._tokens))

    def get_conllu_text(self, include_morphological_tags: bool) -> str:
        """
        Creates string representation of the sentence
        """
        return (f'# sent_id = {self._position}\n'
                f'# text = {self._text}\n' +
                self._format_tokens(include_morphological_tags))

    def get_cleaned_sentence(self) -> str:
        """
        Returns the lowercase representation of the sentence
        """
        return ' '.join((token.get_cleaned() for token in self._tokens))

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
        conllu_sentences = []
        mystem = Mystem()
        sentences = split_by_sentence(text)
        for sent_idx, sentence in enumerate(sentences):
            print(sentence)
            conllu_tokens = []
            tokens = [token for token in mystem.analyze(sentence) if
                      token['text'].strip() and token['text'] not in string.punctuation.replace('.', '')]
            for token_idx, token_info in enumerate(tokens):
                token_text = token_info['text']
                print(token_text)
                token = ConlluToken(token_text)
                token.set_position(token_idx)

                if token_info.get('analysis'):
                    lemma = token_info['analysis'][0]['lex']
                    pos = re.match('^[^,|=]*', token_info['analysis'][0]['gr']).group(0)
                    tags = token_info['analysis'][0]['gr']
                    parameters = MorphologicalTokenDTO(lemma=lemma, pos=pos, tags=tags)
                else:
                    if token_text == '.':
                        pos = 'PUNCT'
                    elif token_text.isdigit():
                        pos = 'NUM'
                    else:
                        pos = 'X'
                    parameters = MorphologicalTokenDTO(lemma=token_text, pos=pos)
                print(token.get_conllu_text(False))
                token.set_morphological_parameters(parameters)
                conllu_tokens.append(token)
            conllu_sentences.append(ConlluSentence(position=sent_idx,
                                                   text=sentence,
                                                   tokens=conllu_tokens))

        return conllu_sentences

    def run(self) -> None:
        """
        Performs basic preprocessing and writes processed text to files
        """
        for val in self._corpus.get_articles().values():
            article = from_raw(val.get_raw_text_path(), val)
            article.set_conllu_sentences(self._process(article.get_raw_text()))
            to_cleaned(article)
            to_conllu(article, include_morphological_tags=True, include_pymorphy_tags=False)


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
    morph_analysis_pipeline = MorphologicalAnalysisPipeline(corpus_manager)
    morph_analysis_pipeline.run()


if __name__ == "__main__":
    main()
