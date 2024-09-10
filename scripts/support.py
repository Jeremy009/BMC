import pandas as pd


def preprocess_frame(df: pd.DataFrame) -> pd.DataFrame:
    """ Typechecking and removal of excessive whitespace. """
    df["Bedrag"] = df["Bedrag"].apply(lambda s: str(s).replace(",", ".").replace("nan", "0.00"))
    df["Bedrag"] = pd.to_numeric(df["Bedrag"], downcast="float")
    df["Omschrijving"] = df["Omschrijving"].apply(reduce_whitespace)
    df["Detail van de omzet"] = df["Detail van de omzet"].apply(reduce_whitespace)
    df["Bericht"] = df["Bericht"].apply(reduce_whitespace)

    return df


def reduce_whitespace(s: str) -> str:
    """ Reduces multiple successive whitespaces to a singel whitespace. """
    return " ".join(str(s).split())


def prune_frame(df: pd.DataFrame) -> pd.DataFrame:
    """ Gets rid of rows which have €0,00 monetary value, and removes uninterresting columns. """
    df = df.drop(df[df["Bedrag"] == 0.0].index)
    df = df.drop(["Rekeningnummer", "Naam van de rekening", "Omzetnummer", "Valutadatum", "Munteenheid"], axis=1)

    return df
