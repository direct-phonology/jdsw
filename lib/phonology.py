import pandas as pd


class NoReadingError(Exception):
    pass


class MultipleReadingsError(Exception):
    pass


class Reconstruction:
    def __init__(self, table: pd.DataFrame) -> None:
        self.table = table.drop_duplicates()

    def initial_for(self, char: str) -> str:
        readings = self.table[self.table["zi"] == char]
        if len(readings) == 0:
            raise NoReadingError
        initials = readings["MCInitial"].unique()
        if len(initials) > 1:
            raise MultipleReadingsError
        return initials[0]

    def final_for(self, char: str) -> str:
        readings = self.table[self.table["zi"] == char]
        if len(readings) == 0:
            raise NoReadingError
        finals = readings["MCfinal"].unique()
        if len(finals) > 1:
            raise MultipleReadingsError
        return finals[0]

    def reading_for(self, char: str) -> str:
        readings = self.table[self.table["zi"] == char]
        if len(readings) == 0:
            raise NoReadingError
        if len(readings) > 1:
            raise MultipleReadingsError
        return readings["MC"].iloc[0]

    def fanqie_reading_for(self, initial: str, final: str) -> str:
        initial_reading = self.initial_for(initial).rstrip("-")
        final_reading = self.final_for(final).lstrip("-")

        # special cases
        # y + j = y
        # yh + j = yh
        if (initial_reading[-1] == "y" and final_reading[0] == "j") or (
            initial_reading[-2:] == "yh" and final_reading[0] == "j"
        ):
            return f"{initial_reading}{final_reading[1:]}"

        # j + j = j
        # j + w = w
        # j + i = i
        if (
            (initial_reading[-1] == "j" and final_reading[0] == "j")
            or (initial_reading[-1] == "j" and final_reading[0] == "w")
            or (initial_reading[-1] == "j" and final_reading[0] == "i")
        ):
            return f"{initial_reading[:-1]}{final_reading}"

        # base case
        return f"{initial_reading}{final_reading}"
