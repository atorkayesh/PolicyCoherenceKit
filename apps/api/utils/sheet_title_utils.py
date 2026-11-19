"""
XLSX sheet titles (label fix L3).

Result titles are built from the sheet label and reserved first; the longest, `Range Influence (Majority Rule)`, is
31 characters. Decision-maker titles replace each of `\\ / ? * [ ] :` with `_`, strip leading and trailing `'`,
fall back to `Sheet`, are cut to 31 characters, and are de-duplicated case-insensitively with ` (2)`, ` (3)`, ...,
cutting the base so the title stays within 31 characters.
"""

from typing import List

from constants.export_constants import RESULT_SHEET_TITLES, SHEET_TITLE_RULES


class SheetTitleBuilder:
    """Builds unique, valid sheet titles."""

    def result_titles(self, sheet_label: str) -> List[str]:
        """
        The four result sheet titles.

        Args:
            sheet_label: Method sheet label, for example `Median Lower`

        Returns:
            List[str]: Aggregated, Coh Scores, Range Influence and Centrality titles
        """
        return [template.format(sl=sheet_label) for template in RESULT_SHEET_TITLES]

    def decision_maker_titles(self, names: List[str], reserved: List[str]) -> List[str]:
        """
        Valid, unique titles for the decision-maker sheets.

        Args:
            names: Decision-maker names, in order
            reserved: Titles already taken (the result titles)

        Returns:
            List[str]: One title per name
        """
        limit = SHEET_TITLE_RULES["MAX_LENGTH"]
        taken = {title.casefold() for title in reserved}
        titles = []
        for name in names:
            base = self.clean(name)
            title = base
            counter = 2
            while title.casefold() in taken:
                suffix = f" ({counter})"
                title = base[: limit - len(suffix)] + suffix
                counter += 1
            taken.add(title.casefold())
            titles.append(title)
        return titles

    def clean(self, name: str) -> str:
        """
        Replace forbidden characters, strip `'`, fall back to `Sheet`, and cut to 31 characters.

        Args:
            name: Decision-maker name

        Returns:
            str: A valid title (not yet unique)
        """
        title = "".join(
            SHEET_TITLE_RULES["REPLACEMENT"] if char in SHEET_TITLE_RULES["FORBIDDEN_CHARACTERS"] else char
            for char in name
        ).strip("'")
        return (title or SHEET_TITLE_RULES["EMPTY_TITLE"])[: SHEET_TITLE_RULES["MAX_LENGTH"]]


sheet_title_builder = SheetTitleBuilder()
