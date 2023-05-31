import re


def merge(*dicts):
    result = {}
    for dict_ in dicts:
        result = result | dict_

    return result


class Box:
    # Extracting ID from labels to classify label type
    types = {
        # all
        "stikskilte": re.compile(r"6\d{7}"),
        # city
        "transformer_city": re.compile(r"T.\s?\d{1,5}\s?-\s?\d\s?-\s?\d{1,2}"),
        "n_delt_skab": re.compile(
            r"(4|6|7)\s?D.?\s?skab\s?\d{1,5}\s?-\s?\d{1,4}", re.IGNORECASE
        ),
        "strækningsskilte": re.compile(
            r"Skab\s?\d{1,5}\s?-\s?\d{1,4}"
        ),  # TODO hvor mange digits efter bindestreg? # TODO Kan man adskille udføringsskab og strækningsskab? # TODO blandes sammen med delte skabe
    }

    def __init__(self, id_) -> None:
        self.id = id_
        self.labels = {}

    def add_label(self, text):
        result = self._get_type(text)
        if result is not None:
            type_, id_, rest = result
            if type_ not in self.labels:
                self.labels[type_] = set()
            id_ = "".join(filter(lambda x: x.isnumeric() or x == "-", id_))
            self.labels[type_].add(Label(type_, id_, rest, text))

    def _get_type(self, text):
        """the type of the label that we seek should be placed before in the word string than other data that we wish to extract"""
        for key, pattern in self.types.items():
            result = re.search(pattern, text)
            if result is not None:
                split = re.split(pattern, text, 1)
                rest = split[-1]
                return (key, result.group(), rest)
        return None

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f"BOX:{self.id}, {self.labels}"

    def __repr__(self):
        return f"{self.id}"

    def __iter__(self):
        for key in self.__dict__:
            if key == "id":
                continue
            yield key, getattr(self, key)

    def asdict(self):
        labels = {}
        for k, v in self.labels.items():
            labels[k] = {}
            for l in v:
                labels[k][l.id] = l.asdict()
        return labels

    @property
    def num_labels(self):
        return len(self.labels)


class Label:
    dimension = {
        "dimension": re.compile(r"\dx\d{2,3}(mm|mm2)?\s?(cu|al)", re.IGNORECASE)
    }  # TODO mm2?? or mm
    ampere = {"ampere": re.compile(r"\d{2,3}\s?A")}
    address = {
        "address": re.compile(r"[A-ZÅÆØ][a-zæøå]{2,}\s\d{1,3}(-\d{0,3})?")
    }  # TODO include multiword address, with and without . e.g. Sdr. Bouleward

    stikskilt = merge(dimension, ampere, address)
    strækningsskilt = merge(dimension, ampere, address)
    transformer = merge(dimension, ampere, address)

    filters = {
        "dimension": lambda x: x.strip().lower(),
        "ampere": lambda x: x.strip().upper(),
        "address": lambda x: x,
    }

    def __init__(self, type_, id_, text, full_text):
        self.id = id_

        if type_ == "stikskilte":
            self.unclassified_text = self._match_data(self.stikskilt, text)
        elif type_ == "strækningsskilte":
            self.unclassified_text = self._match_data(self.strækningsskilt, text)
        elif type_ == "transformer_city":
            self.unclassified_text = self._match_data(self.stikskilt, text)
        elif type_ == "n_delt_skab":
            self.unclassified_text = self._match_data(self.stikskilt, text)
        else:
            self.unclassified_text = text

        if self.unclassified_text.isspace() or not self.unclassified_text:
            self.unclassified_text = None
        self.all_extracted_text = full_text

    def _match_data(self, patterns, text):
        def repl(m):
            replacements.append(m.group(0))
            return ""

        for key, pattern in patterns.items():
            replacements = []
            text = re.sub(pattern, repl, text, 1)
            if replacements:
                cleaned = "".join(map(self.filters[key], replacements[0]))
                setattr(self, key, cleaned)
        return text

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def asdict(self):
        out = dict(vars(self))
        out.pop("id")
        return out