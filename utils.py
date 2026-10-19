"""Small helpers shared by the map tools and the results panel."""


def fmt_number(value, decimals=0):
    """Format a number with a space as the thousands separator, avoiding
    a comma that reads as a decimal separator in German/Austrian locales."""
    return f"{value:,.{decimals}f}".replace(",", " ")


def parse_number(text):
    """Parse a typed number, accepting both '.' and ',' as decimal separator.
    Returns None if the text is not a valid number."""
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None
