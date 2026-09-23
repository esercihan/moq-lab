from decimal import Decimal

from moq_lab.i18n import TRANSLATIONS, format_number, format_percent, translate


def test_language_catalogs_have_identical_keys() -> None:
    assert set(TRANSLATIONS["en"]) == set(TRANSLATIONS["tr"])


def test_turkish_error_translation_formats_details() -> None:
    message = translate(
        "tr",
        "error.capacity_below_demand",
        available=1500,
        demand=1700,
    )

    assert message == "Toplam tedarikçi kapasitesi 1500; 1700 adetlik talebin altında."


def test_unknown_language_falls_back_to_english() -> None:
    assert translate("de", "optimize") == "Optimize purchasing plan"


def test_turkish_number_and_percent_formatting() -> None:
    assert format_number("tr", Decimal("5001885"), decimals=2) == "5.001.885,00"
    assert format_percent("tr", Decimal("0.654")) == "%65,4"
    assert format_number("en", Decimal("5001885"), decimals=2) == "5,001,885.00"
