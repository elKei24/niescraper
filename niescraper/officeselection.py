from typing import List, Tuple, Set

from selenium.webdriver.remote.webelement import WebElement

from niescraper.appointmentchecker import OfficeSelectionStrategy

office_priorities = ["bailen",  # in Valencia
                     "patraix extran",  # in Valencia
                     "oue2",  # in Valencia
                     "oue3",  # in Valencia
                     "alzira",  # 45 min train
                     "sagunto",  # 1:06 h train
                     "expedicion tie",  # 1:30 h train
                     "nie certificados",  # 1:30 h train
                     "onteniente",  # 1:50 h train
                     ]


class NearestValenciaOfficeSelectionStrategy(OfficeSelectionStrategy):
    def select_province(self, provinces: List[WebElement]) -> None:
        next(province for province in provinces if "valencia" in province.text.lower()).click()

    @staticmethod
    def find_office(offices: List[WebElement]) -> WebElement:
        for priority in office_priorities:
            try:
                return next(office for office in offices if priority.lower() in office.text.lower())
            except StopIteration:
                pass
        return offices[0]

    def select_office(self, offices: List[WebElement]) -> None:
        self.find_office(offices).click()


class SpecificOfficeSelectionStrategy(OfficeSelectionStrategy):
    def __init__(self, province: str, office: str):
        self.province = province
        self.office = office

    def select_province(self, provinces: List[WebElement]) -> None:
        next(province for province in provinces
             if self.province.lower().strip() in province.text.lower().strip()).click()

    def select_office(self, offices: List[WebElement]) -> None:
        next(office for office in offices if self.office.lower().strip() in office.text.lower().strip()).click()

    def pre_select_office(self, offices: List[WebElement]) -> None:
        self.select_office(offices)


class ManualOfficeSelectionStrategy(OfficeSelectionStrategy):
    @staticmethod
    def _click_single_or_pause(options: List[WebElement], message: str) -> None:
        if len(options) == 1:
            options[0].click()
            return
        input(message)

    def select_office(self, offices: List[WebElement]) -> None:
        self._click_single_or_pause(offices, "Select the office in the browser and press Enter to continue...")

    def select_province(self, provinces: List[WebElement]) -> None:
        self._click_single_or_pause(provinces, "Select the province in the browser and press Enter to continue...")


class DFSOfficeSelectionStrategy(OfficeSelectionStrategy):
    def __init__(self):
        self.last_province: str
        self.last_office: str
        self.finished_offices: Set[Tuple[str, str]] = set()
        self.finished_provinces: Set[str] = set()
        self.last_province_reached_office_selection: bool

    def select_province(self, provinces: List[WebElement]) -> None:
        for province in provinces:
            if province.text not in self.finished_provinces:
                self.last_province = province.text
                province.click()
                self.last_province_reached_office_selection = False # reset flag
                return
        raise DFSOfficeSelectionStrategy.NoMoreProvincesException()

    def select_office(self, offices: List[WebElement]) -> None:
        # remember that this province has offices so that we do not ignore it only because we do not find an
        # appointment right away
        self.last_province_reached_office_selection = True

        # find the offices we have not yet visited
        unvisited_offices = {office for office in offices
                             if not (self.last_province, office.text) in self.finished_offices}

        # All offices visited? Cancel
        if len(unvisited_offices) == 0:
            self.finished_provinces.add(self.last_province)
            raise DFSOfficeSelectionStrategy.NoMoreOfficesException()

        # Select the first office we have not visited so far and remember it
        office = unvisited_offices.pop()
        self.last_office = office.text
        self.finished_offices.add((self.last_province, office.text))
        office.click()

        # If this was the last office of this province, we can ignore the province
        if not unvisited_offices:
            self.finished_provinces.add(self.last_province)

    def notify_about_no_appointments_for_last_selection(self):
        # Handle the case that we did not even reach the office selection and therefore also did not already kick out
        # the province
        if not self.last_province_reached_office_selection:
            self.finished_provinces.add(self.last_province)

    class NoMoreOfficesException(Exception):
        pass

    class NoMoreProvincesException(Exception):
        pass
