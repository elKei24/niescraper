from typing import Iterable

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement


def _normalize_option_text(text: str) -> str:
    return text.lower().translate(str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouaeiounn", ".;,:¿?¡!¿¡"))


def find_assign_nie_option(options: Iterable[WebElement]) -> WebElement:
    for option in options:
        text = _normalize_option_text(option.text)
        if "asignacion" in text and "nie" in text:
            return option
    raise NoSuchElementException("No option for NIE assignment found")


def find_register_eu_citizen_option(options: Iterable[WebElement]) -> WebElement:
    for option in options:
        text = _normalize_option_text(option.text)
        if "registro" in text and "ciudadano de la ue" in text:
            return option
    raise NoSuchElementException("No option for EU citizen registration found")
