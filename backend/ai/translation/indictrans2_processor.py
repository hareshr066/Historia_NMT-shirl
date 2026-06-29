import re
import copy
from typing import List, Tuple, Union

# Import components from indicnlp and sacremoses
from indicnlp.tokenize import indic_tokenize, indic_detokenize
from indicnlp.normalize.indic_normalize import IndicNormalizerFactory
from sacremoses import MosesPunctNormalizer, MosesTokenizer, MosesDetokenizer
from indicnlp.transliterate.unicode_transliterate import UnicodeIndicTransliterator

class IndicProcessor:
    def __init__(self, inference=True):
        self.inference = inference

        self._flores_codes = {
            "asm_Beng": "as",
            "awa_Deva": "hi",
            "ben_Beng": "bn",
            "bho_Deva": "hi",
            "brx_Deva": "hi",
            "doi_Deva": "hi",
            "eng_Latn": "en",
            "gom_Deva": "kK",
            "gon_Deva": "hi",
            "guj_Gujr": "gu",
            "hin_Deva": "hi",
            "hne_Deva": "hi",
            "kan_Knda": "kn",
            "kas_Arab": "ur",
            "kas_Deva": "hi",
            "kha_Latn": "en",
            "lus_Latn": "en",
            "mag_Deva": "hi",
            "mai_Deva": "hi",
            "mal_Mlym": "ml",
            "mar_Deva": "mr",
            "mni_Beng": "bn",
            "mni_Mtei": "hi",
            "npi_Deva": "ne",
            "ory_Orya": "or",
            "pan_Guru": "pa",
            "san_Deva": "hi",
            "sat_Olck": "or",
            "snd_Arab": "ur",
            "snd_Deva": "hi",
            "tam_Taml": "ta",
            "tel_Telu": "te",
            "urd_Arab": "ur",
            "unr_Deva": "hi",
        }

        self._indic_num_map = {
            "\u09e6": "0", "0": "0", "\u0ae6": "0", "\u0ce6": "0", "\u0966": "0", "\u0660": "0", "\uabf0": "0", "\u0b66": "0", "\u0a66": "0", "\u1c50": "0", "\u06f0": "0",
            "\u09e7": "1", "1": "1", "\u0ae7": "1", "\u0967": "1", "\u0ce7": "1", "\u06f1": "1", "\uabf1": "1", "\u0b67": "1", "\u0a67": "1", "\u1c51": "1", "\u0c67": "1",
            "\u09e8": "2", "2": "2", "\u0ae8": "2", "\u0968": "2", "\u0ce8": "2", "\u06f2": "2", "\uabf2": "2", "\u0b68": "2", "\u0a68": "2", "\u1c52": "2", "\u0c68": "2",
            "\u09e9": "3", "3": "3", "\u0ae9": "3", "\u0969": "3", "\u0ce9": "3", "\u06f3": "3", "\uabf3": "3", "\u0b69": "3", "\u0a69": "3", "\u1c53": "3", "\u0c69": "3",
            "\u09ea": "4", "4": "4", "\u0aea": "4", "\u096a": "4", "\u0cea": "4", "\u06f4": "4", "\uabf4": "4", "\u0b6a": "4", "\u0a6a": "4", "\u1c54": "4", "\u0c6a": "4",
            "\u09eb": "5", "5": "5", "\u0aeb": "5", "\u096b": "5", "\u0ceb": "5", "\u06f5": "5", "\uabf5": "5", "\u0b6b": "5", "\u0a6b": "5", "\u1c55": "5", "\u0c6b": "5",
            "\u09ec": "6", "6": "6", "\u0aec": "6", "\u096c": "6", "\u0cec": "6", "\u06f6": "6", "\uabf6": "6", "\u0b6c": "6", "\u0a6c": "6", "\u1c56": "6", "\u0c6c": "6",
            "\u09ed": "7", "7": "7", "\u0aed": "7", "\u096d": "7", "\u0ced": "7", "\u06f7": "7", "\uabf7": "7", "\u0b6d": "7", "\u0a6d": "7", "\u1c57": "7", "\u0c6d": "7",
            "\u09ee": "8", "8": "8", "\u0aee": "8", "\u096e": "8", "\u0cee": "8", "\u06f8": "8", "\uabf8": "8", "\u0b6e": "8", "\u0a6e": "8", "\u1c58": "8", "\u0c6e": "8",
            "\u09ef": "9", "9": "9", "\u0aef": "9", "\u096f": "9", "\u0cef": "9", "\u06f9": "9", "\uabf9": "9", "\u0b6f": "9", "\u0a6f": "9", "\u1c59": "9", "\u0c6f": "9",
        }

        self._placeholder_entity_maps = []

        self._en_tok = MosesTokenizer(lang="en")
        self._en_normalizer = MosesPunctNormalizer()
        self._en_detok = MosesDetokenizer(lang="en")
        self._xliterator = UnicodeIndicTransliterator()

        self._multispace_regex = re.compile("[ ]{2,}")
        self._digit_space_percent = re.compile(r"(\d) %")
        self._double_quot_punc = re.compile(r"\"([,\.]+)")
        self._digit_nbsp_digit = re.compile(r"(\d) (\d)")
        self._end_bracket_space_punc_regex = re.compile(r"\) ([\.!:?;,])")

        self._URL_PATTERN = r"\b(?<![\w/.])(?:(?:https?|ftp)://)?(?:(?:[\w-]+\.)+(?!\.))(?:[\w/\-?#&=%.]+)+(?!\.\w+)\b"
        self._NUMERAL_PATTERN = r"(~?\d+\.?\d*\s?%?\s?-?\s?~?\d+\.?\d*\s?%|~?\d+%|\d+[-\/.,:']\d+[-\/.,:'+]\d+(?:\.\d+)?|\d+[-\/.:'+]\d+(?:\.\d+)?)"
        self._EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"
        self._OTHER_PATTERN = r"[A-Za-z0-9]*[#|@]\w+"

    def _add_placeholder_entity_map(self, placeholder_entity_map):
        self._placeholder_entity_maps.append(placeholder_entity_map)

    def get_placeholder_entity_maps(self, clear_ple_maps=False):
        if not clear_ple_maps:
            return self._placeholder_entity_maps
        else:
            ple_maps = copy.deepcopy(self._placeholder_entity_maps)
            self._placeholder_entity_maps.clear()
            return ple_maps

    def _punc_norm(self, text) -> str:
        text = (
            text.replace("\r", "")
            .replace("(", " (")
            .replace(")", ") ")
            .replace("( ", "(")
            .replace(" )", ")")
            .replace(" :", ":")
            .replace(" ;", ";")
            .replace("`", "'")
            .replace("„", '"')
            .replace("“", '"')
            .replace("”", '"')
            .replace("–", "-")
            .replace("—", " - ")
            .replace("´", "'")
            .replace("‘", "'")
            .replace("‚", "'")
            .replace("’", "'")
            .replace("''", '"')
            .replace("´´", '"')
            .replace("…", "...")
            .replace(" « ", ' "')
            .replace("« ", '"')
            .replace("«", '"')
            .replace(" » ", '" ')
            .replace(" »", '"')
            .replace("»", '"')
            .replace(" %", "%")
            .replace("nº ", "nº ")
            .replace(" :", ":")
            .replace(" ºC", " ºC")
            .replace(" cm", " cm")
            .replace(" ?", "?")
            .replace(" !", "!")
            .replace(" ;", ";")
            .replace(", ", ", ")
        )
        text = self._multispace_regex.sub(" ", text)
        text = self._end_bracket_space_punc_regex.sub(r")\1", text)
        text = self._digit_space_percent.sub(r"\1%", text)
        text = self._double_quot_punc.sub(r'\1"', text)
        text = self._digit_nbsp_digit.sub(r"\1.\2", text)
        return text.strip()

    def _normalize_indic_numerals(self, line: str) -> str:
        return "".join([self._indic_num_map.get(c, c) for c in line])

    def _wrap_with_placeholders(self, text: str, patterns: list) -> str:
        serial_no = 1
        placeholder_entity_map = dict()
        indic_failure_cases = [
            "آی ڈی ", "ꯑꯥꯏꯗꯤ", "आईडी", "आई . डी . ", "आई . डी .", "आई. डी. ", "आई. डी.",
            "ऐटि", "آئی ڈی ", "ᱟᱭᱰᱤ ᱾", "आयडी", "ऐडि", "आइडि", "ᱟᱭᱰᱤ",
        ]
        for pattern in patterns:
            matches = set(re.findall(pattern, text))
            for match in matches:
                if pattern == self._URL_PATTERN:
                    if len(match.replace(".", "")) < 4:
                        continue
                if pattern == self._NUMERAL_PATTERN:
                    if len(match.replace(" ", "").replace(".", "").replace(":", "")) < 4:
                        continue

                base_placeholder = f"<ID{serial_no}>"
                placeholder_entity_map[f"<ID{serial_no}]"] = match
                placeholder_entity_map[f"< ID{serial_no} ]"] = match
                placeholder_entity_map[f"<ID{serial_no}>"] = match
                placeholder_entity_map[f"< ID{serial_no} >"] = match

                for i in indic_failure_cases:
                    placeholder_entity_map[f"<{i}{serial_no}>"] = match
                    placeholder_entity_map[f"< {i}{serial_no} >"] = match
                    placeholder_entity_map[f"< {i} {serial_no} >"] = match
                    placeholder_entity_map[f"<{i} {serial_no}]"] = match
                    placeholder_entity_map[f"< {i} {serial_no} ]"] = match
                    placeholder_entity_map[f"[{i} {serial_no}]"] = match
                    placeholder_entity_map[f"[ {i} {serial_no} ]"] = match

                text = text.replace(match, base_placeholder)
                serial_no += 1

        text = re.sub(r"\s+", " ", text).replace(">/", ">").replace("]/", "]")
        self._add_placeholder_entity_map(placeholder_entity_map)
        return text

    def _normalize(self, text: str) -> str:
        patterns = [
            self._EMAIL_PATTERN,
            self._URL_PATTERN,
            self._NUMERAL_PATTERN,
            self._OTHER_PATTERN,
        ]
        text = self._normalize_indic_numerals(text.strip())
        if self.inference:
            text = self._wrap_with_placeholders(text, patterns)
        return text

    def _apply_lang_tags(self, sents: List[str], src_lang: str, tgt_lang: str, delimiter=" ") -> List[str]:
        return [f"{src_lang}{delimiter}{tgt_lang}{delimiter}{x.strip()}" for x in sents]

    def _preprocess(self, sent: str, lang: str, normalizer) -> str:
        iso_lang = self._flores_codes[lang]
        sent = self._punc_norm(sent)
        sent = self._normalize(sent)

        transliterate = True
        if lang.split("_")[1] in ["Arab", "Aran", "Olck", "Mtei", "Latn"]:
            transliterate = False

        if iso_lang == "en":
            processed_sent = " ".join(
                self._en_tok.tokenize(
                    self._en_normalizer.normalize(sent.strip()), escape=False
                )
            )
        elif transliterate:
            processed_sent = self._xliterator.transliterate(
                " ".join(
                    indic_tokenize.trivial_tokenize(
                        normalizer.normalize(sent.strip()), iso_lang
                    )
                ),
                iso_lang,
                "hi",
            ).replace(" ् ", "्")
        else:
            processed_sent = " ".join(
                indic_tokenize.trivial_tokenize(
                    normalizer.normalize(sent.strip()), iso_lang
                )
            )
        return processed_sent

    def preprocess_batch(self, batch: List[str], src_lang: str, tgt_lang: str, is_target: bool = False) -> List[str]:
        # Reset placeholder map if starting a new batch
        if not is_target:
            self._placeholder_entity_maps.clear()

        normalizer = (
            IndicNormalizerFactory().get_normalizer(self._flores_codes[src_lang])
            if src_lang != "eng_Latn"
            else None
        )
        preprocessed_sents = [
            self._preprocess(sent, src_lang, normalizer) for sent in batch
        ]
        tagged_sents = (
            self._apply_lang_tags(preprocessed_sents, src_lang, tgt_lang)
            if not is_target
            else preprocessed_sents
        )
        return tagged_sents

    def _postprocess(self, sent: str, placeholder_entity_map: dict, lang: str = "hin_Deva") -> str:
        lang_code, script_code = lang.split("_")
        iso_lang = self._flores_codes[lang]

        if script_code in ["Arab", "Aran"]:
            sent = (
                sent.replace(" ؟", "?")
                .replace(" ۔", ".")
                .replace(" ،", ",")
                .replace("ٮ۪", "ؠ")
            )
        if lang_code == "ory":
            sent = sent.replace("ଯ଼", "ୟ")

        for k, v in placeholder_entity_map.items():
            sent = sent.replace(k, v)

        return (
            self._en_detok.detokenize(sent.split(" "))
            if lang == "eng_Latn"
            else indic_detokenize.trivial_detokenize(
                self._xliterator.transliterate(sent, "hi", iso_lang),
                iso_lang,
            )
        )

    def postprocess_batch(self, sents: List[str], lang: str = "hin_Deva", placeholder_entity_maps=None) -> List[str]:
        if not placeholder_entity_maps:
            placeholder_entity_maps = self.get_placeholder_entity_maps()

        postprocessed_sents = []
        for i, sent in enumerate(sents):
            pe_map = placeholder_entity_maps[i] if i < len(placeholder_entity_maps) else {}
            postprocessed_sents.append(self._postprocess(sent, pe_map, lang))

        self._placeholder_entity_maps.clear()
        return postprocessed_sents
