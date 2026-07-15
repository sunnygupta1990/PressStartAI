import re


class AITextCleaner:
    """Clean cosmetic repetition artifacts from local AI text."""

    REPEATED_WORD_PATTERN = re.compile(
        r"\b(\w+)\s+\1\b",
        flags=re.IGNORECASE | re.UNICODE,
    )

    REPEATED_PHRASE_PATTERN = re.compile(
        r"\b(.{3,40}?)\s+\1\b",
        flags=re.IGNORECASE | re.UNICODE,
    )

    DUPLICATED_QUOTE_PATTERN = re.compile(
        r"(['\"])([^'\"]{2,40})\1\s+\1\2\1",
        flags=re.IGNORECASE | re.UNICODE,
    )

    def clean(
        self,
        text: str,
    ) -> str:
        cleaned = text.strip()

        previous = None

        while cleaned != previous:
            previous = cleaned

            cleaned = self.REPEATED_WORD_PATTERN.sub(
                r"\1",
                cleaned,
            )

            cleaned = self.REPEATED_PHRASE_PATTERN.sub(
                r"\1",
                cleaned,
            )

            cleaned = self.DUPLICATED_QUOTE_PATTERN.sub(
                r"\1\2\1",
                cleaned,
            )

            cleaned = self._remove_partial_word_duplicates(
                cleaned
            )

        cleaned = re.sub(
            r"\s{2,}",
            " ",
            cleaned,
        )

        return cleaned.strip()

    @staticmethod
    def _remove_partial_word_duplicates(
        text: str,
    ) -> str:
        words = text.split()

        if len(words) < 2:
            return text

        cleaned_words: list[str] = []

        for word in words:
            if not cleaned_words:
                cleaned_words.append(
                    word
                )
                continue

            previous_word = cleaned_words[-1]

            previous_core = AITextCleaner._word_core(
                previous_word
            )

            current_core = AITextCleaner._word_core(
                word
            )

            is_partial_duplicate = (
                len(previous_core) >= 1
                and len(current_core) > len(previous_core)
                and current_core.lower().startswith(
                    previous_core.lower()
                )
            )

            if is_partial_duplicate:
                cleaned_words[-1] = word
                continue

            cleaned_words.append(
                word
            )

        return " ".join(
            cleaned_words
        )

    @staticmethod
    def _word_core(
        word: str,
    ) -> str:
        return re.sub(
            r"^\W+|\W+$",
            "",
            word,
            flags=re.UNICODE,
        )