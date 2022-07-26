import pandas as pd


class NoReadingError(Exception):
    pass


class MultipleReadingsError(Exception):
    pass


class Reconstruction:
    def __init__(self, table: pd.DataFrame) -> None:
        self.table = table.drop_duplicates()

    def initial_for(self, char: str) -> str:
        readings = self.table[self.table["char"] == char]
        if len(readings) == 0:
            raise NoReadingError(f"No reading for {char}")
        initials = readings["initial"].unique()
        if len(initials) > 1:
            raise MultipleReadingsError(f"Multiple initials for {char}")
        return initials[0]

    def rime_for(self, char: str) -> str:
        readings = self.table[self.table["char"] == char]
        if len(readings) == 0:
            raise NoReadingError(f"No reading for {char}")
        rimes = readings["rime"].unique()
        if len(rimes) > 1:
            raise MultipleReadingsError(f"Multiple rimes for {char}")
        return rimes[0]

    def reading_for(self, char: str) -> str:
        readings = self.table[self.table["char"] == char]
        if len(readings) == 0:
            raise NoReadingError(f"No reading for {char}")
        if len(readings) > 1:
            raise MultipleReadingsError(f"Multiple readings for {char}")
        return readings["reading"].iloc[0]

    def readings_for(self, char: str) -> list[str]:
        return self.table[self.table["char"] == char]["reading"].unique().tolist()

    def fanqie_reading_for(self, initial: str, final: str) -> str:
        initial_reading = self.initial_for(initial)
        rime_reading = self.rime_for(final)

        # special cases
        # y + j = y
        # yh + j = yh
        if (initial_reading[-1] == "y" and rime_reading[0] == "j") or (
            initial_reading[-2:] == "yh" and rime_reading[0] == "j"
        ):
            return f"{initial_reading}{rime_reading[1:]}"

        # j + j = j
        # j + w = w
        # j + i = i
        if (
            (initial_reading[-1] == "j" and rime_reading[0] == "j")
            or (initial_reading[-1] == "j" and rime_reading[0] == "w")
            or (initial_reading[-1] == "j" and rime_reading[0] == "i")
        ):
            return f"{initial_reading[:-1]}{rime_reading}"

        # base case
        return f"{initial_reading}{rime_reading}"

    def is_valid_reading(self, char: str, reading: str) -> bool:
        return reading in self.readings_for(char)
