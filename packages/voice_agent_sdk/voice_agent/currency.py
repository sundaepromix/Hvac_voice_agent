"""Spoken-number guidance per currency.

Text-to-speech reads "1500000" digit-by-digit ("one five zero zero zero...")
unless you tell the model how humans actually say large amounts — and that
differs by region (western thousand/million vs. South-Asian lakh/crore). This
table was embedded in the receptionist prompt module; it's pure data and
reusable by any voice agent that quotes prices, so it lives on its own here.
"""
from __future__ import annotations

_WESTERN_TEMPLATE = (
    "Currency is {name}. Say '{spoken}'. Use natural English number-speaking: "
    "'twelve hundred {spoken}', 'fifteen thousand {spoken}', 'two and a half "
    "million {spoken}'. Round generously when speaking ('around fifteen "
    "thousand'). NEVER read digits one by one."
)
_SOUTH_ASIAN_TEMPLATE = (
    "Currency is {name}. Say '{spoken}'. Use the South Asian lakh/crore "
    "system: 'fifteen lakh {spoken}' (1,500,000), 'sixteen lakh fifty thousand' "
    "(1,650,000), 'one crore {spoken}' (10,000,000), 'two and a half crore' "
    "(25,000,000). NEVER say 'one million five hundred thousand' — say "
    "'fifteen lakh'. NEVER read digit by digit."
)

_WESTERN: dict[str, tuple[str, str]] = {
    "USD": ("US Dollars", "dollars"), "EUR": ("Euros", "euros"),
    "GBP": ("British Pounds", "pounds"), "CAD": ("Canadian Dollars", "dollars"),
    "AUD": ("Australian Dollars", "dollars"), "NZD": ("New Zealand Dollars", "dollars"),
    "CHF": ("Swiss Francs", "francs"), "SEK": ("Swedish Kronor", "kronor"),
    "NOK": ("Norwegian Kroner", "kroner"), "DKK": ("Danish Kroner", "kroner"),
    "PLN": ("Polish Zloty", "zloty"), "CZK": ("Czech Koruna", "koruna"),
    "HUF": ("Hungarian Forint", "forint"), "RON": ("Romanian Lei", "lei"),
    "TRY": ("Turkish Lira", "lira"), "RUB": ("Russian Rubles", "rubles"),
    "UAH": ("Ukrainian Hryvnia", "hryvnia"), "ILS": ("Israeli Shekels", "shekels"),
    "AED": ("UAE Dirhams", "dirhams"), "SAR": ("Saudi Riyals", "riyals"),
    "QAR": ("Qatari Riyals", "riyals"), "KWD": ("Kuwaiti Dinars", "dinars"),
    "BHD": ("Bahraini Dinars", "dinars"), "OMR": ("Omani Rials", "rials"),
    "JOD": ("Jordanian Dinars", "dinars"), "EGP": ("Egyptian Pounds", "pounds"),
    "LBP": ("Lebanese Pounds", "pounds"), "MAD": ("Moroccan Dirhams", "dirhams"),
    "DZD": ("Algerian Dinars", "dinars"), "TND": ("Tunisian Dinars", "dinars"),
    "ZAR": ("South African Rand", "rand"), "NGN": ("Nigerian Naira", "naira"),
    "KES": ("Kenyan Shillings", "shillings"), "GHS": ("Ghanaian Cedi", "cedi"),
    "ETB": ("Ethiopian Birr", "birr"), "UGX": ("Ugandan Shillings", "shillings"),
    "TZS": ("Tanzanian Shillings", "shillings"), "CNY": ("Chinese Yuan", "yuan"),
    "HKD": ("Hong Kong Dollars", "dollars"), "TWD": ("Taiwan Dollars", "dollars"),
    "JPY": ("Japanese Yen", "yen"), "KRW": ("Korean Won", "won"),
    "SGD": ("Singapore Dollars", "dollars"), "MYR": ("Malaysian Ringgit", "ringgit"),
    "IDR": ("Indonesian Rupiah", "rupiah"), "PHP": ("Philippine Pesos", "pesos"),
    "THB": ("Thai Baht", "baht"), "VND": ("Vietnamese Dong", "dong"),
    "MXN": ("Mexican Pesos", "pesos"), "BRL": ("Brazilian Reais", "reais"),
    "ARS": ("Argentine Pesos", "pesos"), "CLP": ("Chilean Pesos", "pesos"),
    "COP": ("Colombian Pesos", "pesos"), "PEN": ("Peruvian Sol", "sol"),
    "UYU": ("Uruguayan Pesos", "pesos"),
}
_SOUTH_ASIAN: dict[str, tuple[str, str]] = {
    "PKR": ("Pakistani Rupees", "rupees"), "INR": ("Indian Rupees", "rupees"),
    "BDT": ("Bangladeshi Taka", "taka"), "LKR": ("Sri Lankan Rupees", "rupees"),
    "NPR": ("Nepalese Rupees", "rupees"), "AFN": ("Afghan Afghani", "afghani"),
}

SPEAKING_GUIDES: dict[str, str] = {}
for _code, (_name, _spoken) in _WESTERN.items():
    SPEAKING_GUIDES[_code] = _WESTERN_TEMPLATE.format(name=_name, spoken=_spoken)
for _code, (_name, _spoken) in _SOUTH_ASIAN.items():
    SPEAKING_GUIDES[_code] = _SOUTH_ASIAN_TEMPLATE.format(name=_name, spoken=_spoken)


def speaking_guide(code: str) -> str:
    """Return the spoken-number guidance for an ISO-4217 code, with a safe
    generic fallback for currencies not in the table."""
    code = (code or "USD").upper()
    return SPEAKING_GUIDES.get(
        code,
        f"Currency code is {code}. Speak amounts naturally — never digit by digit.",
    )
