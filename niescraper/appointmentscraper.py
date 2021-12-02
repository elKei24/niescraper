from datetime import datetime, date, time
from typing import Sequence

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


def scrape_appointments(driver: WebDriver) -> Sequence[datetime]:
    box_appointments = driver.find_elements(by='xpath', value="//label[contains(@id, 'lCita_')]")
    if box_appointments:
        return _scrape_box_appointments(box_appointments)

    try:
        table_appointments = driver.find_element(value="VistaMapa_Datatable")
        return _scrape_table_appointments(table_appointments)
    except NoSuchElementException:
        return []


def _scrape_box_appointments(box_appointments: Sequence[WebElement]) -> Sequence[datetime]:
    for appointment in box_appointments:
        lines = appointment.text.split('\n', 2)
        appointment_date = lines[1].split(' ', 1)[1]
        (day, month, year) = appointment_date.split('/')
        appointment_time = lines[2].split(' ', 1)[1]
        (hour, minute) = appointment_time.split(':')
        yield datetime(int(year), int(month), int(day), int(hour), int(minute))


def _scrape_table_appointments(table: WebElement) -> Sequence[datetime]:
    heads = [th for th in table.find_elements(by=By.TAG_NAME, value='th') if th.text]
    dates = [datetime.strptime(head.text, '%d/%m/%Y').date() for head in heads]
    for row in table.find_element(by=By.TAG_NAME, value="tbody").find_elements(by=By.TAG_NAME, value='tr'):
        tds = row.find_elements(by=By.TAG_NAME, value='td')
        appointment_time = datetime.strptime(tds[0].text, '%H:%M').time()
        for appointment_date, td in zip(dates, tds[1:]):
            if "libre" in td.text.lower():
                yield datetime.combine(appointment_date, appointment_time)
