import abc
from enum import auto, unique, Enum
from time import sleep
from typing import List, Callable, Dict, Optional, Mapping, Iterator

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

url = "https://icp.administracionelectronica.gob.es/icpplus/index.html"


class OfficeSelectionStrategy(abc.ABC):
    @abc.abstractmethod
    def select_province(self, provinces: List[WebElement]) -> None:
        pass

    @abc.abstractmethod
    def select_office(self, offices: List[WebElement]) -> None:
        pass

    def pre_select_office(self, offices: List[WebElement]) -> None:
        """Selects an office right after selecting the province.
        This can be useful for appointments that require a specific office, e.g. registration as EU citizen.
        Otherwise, this method can just do nothing and let select_office() handle the selection later.
        """
        pass


IntentionSelectionStrategy = Callable[[List[WebElement]], WebElement]


@unique
class FormField(Enum):
    PassportId = auto()
    NieNumber = auto()
    Name = auto()
    YearOfBirth = auto()
    NativeCountry = auto()
    PhoneNumber = auto()
    Email = auto()
    AdditionalNotes = auto()


@unique
class IdentificationMethod(Enum):
    ByDNI = "rdbTipoDocDni"
    ByNIE = "rdbTipoDocNie"
    ByPassport = "rdbTipoDocPas"


class FormValues(Mapping[FormField, Optional[str]]):
    def __init__(self, identification_method: IdentificationMethod, data: Dict[FormField, str] = None):
        if data is None:
            data = dict()
        self.identification_method = identification_method
        self._data = data

    @property
    def identifier(self) -> Optional[str]:
        if self.identification_method is IdentificationMethod.ByDNI:
            return self[FormField.PassportId]
        elif self.identification_method is IdentificationMethod.ByNIE:
            return self[FormField.NieNumber]
        elif self.identification_method is IdentificationMethod.ByPassport:
            return self[FormField.PassportId]
        raise NotImplementedError(f"Identifier deviation for {self.identification_method} not implemented")

    def __getitem__(self, k: FormField) -> Optional[str]:
        return self._data.get(k, None)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[FormField]:
        return self._data.__iter__()


class AppointmentChecker:
    def __init__(self, slow: bool = False):
        self.slow = slow
        self._driver: Optional[WebDriver] = None

    @property
    def driver(self) -> WebDriver:
        if self._driver is not None:
            return self._driver
        driver = webdriver.Firefox()
        self._driver = driver
        return driver

    def _wait_if_slow(self):
        if self.slow:
            sleep(2)

    def _scroll_into_view(self, element):
        # sometimes the cookie banner is in the way; do not accept or rate limits will apply
        try:
            cookie_element = self.driver.find_element(value="cookie-law-info-bar")
            self.driver.execute_script("arguments[0].remove();", cookie_element)
        except NoSuchElementException:
            pass
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def _scroll_and_click(self, element):
        self._scroll_into_view(element)
        element.click()

    def _fill_input_if_present(self, input_id: str, value: Optional[str]):
        if not value:
            return
        try:
            self.driver.find_element(value=input_id).send_keys(value)
        except NoSuchElementException:
            pass

    def _fill_applicant_data(self, form_values: FormValues):
        self._scroll_and_click(self.driver.find_element(value=form_values.identification_method.value))
        self._fill_input_if_present("txtIdCitado", form_values.identifier)
        self._fill_input_if_present("txtDesCitado", form_values[FormField.Name])
        self._fill_input_if_present("txtAnnoCitado", form_values[FormField.YearOfBirth])
        try:
            countries = self.driver.find_elements(by=By.XPATH,
                                                  value="//select[@id = 'txtPaisNac']/option[text() != '']")
            native_country = form_values[FormField.NativeCountry]
            self._scroll_and_click(next(country for country in countries if
                                        country.text.lower().strip() == native_country.lower().strip()))
        except StopIteration:
            pass
        self._wait_if_slow()
        self._scroll_and_click(self.driver.find_element(value="btnEnviar"))

    def _fill_additional_info(self, form_values: FormValues):
        self._fill_input_if_present("txtTelefonoCitado", form_values[FormField.PhoneNumber])
        self._fill_input_if_present("emailUNO", form_values[FormField.Email])
        self._fill_input_if_present("emailDOS", form_values[FormField.Email])
        self._fill_input_if_present("txtObservaciones", form_values[FormField.AdditionalNotes])
        self._wait_if_slow()
        self._scroll_and_click(self.driver.find_element(value="btnSiguiente"))

    def _select_province(self, selection_strategy: OfficeSelectionStrategy):
        def find_provinces():
            return self.driver.find_elements(by=By.XPATH, value="//select[@id = 'form']/option[@value != '']")

        provinces = find_provinces()
        if not provinces and \
                self.driver.find_elements(by=By.XPATH, value="//*[@id='prov_selecc']"):
            self._scroll_and_click(self.driver.find_element(value="btnVolver"))
            provinces = find_provinces()
        selection_strategy.select_province(provinces)
        self._wait_if_slow()
        self.driver.find_element(value="btnAceptar").click()

    def check_citas_available(self, form_values: FormValues, office_strategy: OfficeSelectionStrategy,
                              intention_strategy: IntentionSelectionStrategy):
        self.driver.get(url)
        self._select_province(office_strategy)
        offices = self.driver.find_elements(by=By.XPATH,
                                            value="//select[@id = 'sede']/optgroup/option[@value != '' and @value != '99']")
        office_strategy.pre_select_office(offices)

        for attempts in range(5, -1, -1):
            try:
                options = self.driver.find_elements(by=By.XPATH, value="//select[contains(@id, 'tramiteGrupo[')]/"
                                                                       "option[@value >= 0]")
                self._scroll_and_click(intention_strategy(options))
                break
            except (NoSuchElementException, StaleElementReferenceException) as e:
                if attempts:
                    sleep(0.1)
                else:
                    raise e
        self._wait_if_slow()
        self.driver.find_element(value="btnAceptar").click()

        self._wait_if_slow()
        self._scroll_and_click(self.driver.find_element(value="btnEntrar"))

        self._fill_applicant_data(form_values)
        self._wait_if_slow()
        self._scroll_and_click(self.driver.find_element(value="btnEnviar"))

        try:
            self.driver.find_element(by=By.XPATH,
                                     value="//*[contains(text(), 'En este momento no hay citas disponibles')]")
            self._wait_if_slow()
            return False
        except NoSuchElementException:
            pass

        if self.driver.find_elements(by=By.XPATH, value="//select[@id = 'idSede']"):
            offices = self.driver.find_elements(by=By.XPATH, value="//select[@id = 'idSede']/option[@value != '']")
            office_strategy.select_office(offices)
            self._wait_if_slow()
            self._scroll_and_click(self.driver.find_element(value="btnSiguiente"))

        self._fill_additional_info(form_values)
        self._wait_if_slow()
        return True

    def __del__(self):
        if self._driver is not None:
            self._driver.quit()
            self._driver = None
