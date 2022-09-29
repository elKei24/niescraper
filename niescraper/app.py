import argparse
import datetime
import sys
import traceback
from time import sleep

import pytz
from selenium.common.exceptions import NoSuchElementException

from niescraper.alarm import play_alarm_until_input
from niescraper.appointmentchecker import AppointmentChecker, FormValues, IdentificationMethod, FormField, \
    IntentionSelectionStrategy, OfficeSelectionStrategy
from niescraper.appointmentscraper import scrape_appointments
from niescraper.intentionselection import find_assign_nie_option, find_register_eu_citizen_option
from niescraper.officeselection import NearestValenciaOfficeSelectionStrategy, ManualOfficeSelectionStrategy, \
    DFSOfficeSelectionStrategy, SpecificOfficeSelectionStrategy

form_values = FormValues(IdentificationMethod.ByNIE, {
    FormField.NieNumber: "Y1234567X",
    FormField.PassportId: "PASSP_ID",
    FormField.Name: "My Name",
    FormField.Email: "mail@example.org",
    FormField.PhoneNumber: "123456789",
    FormField.NativeCountry: "Alemania",
    FormField.YearOfBirth: "2022",
})


def print_with_time(text):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + text)


def seconds_until_next_check(now: datetime.datetime = None):
    tz = pytz.timezone('Europe/Madrid')
    if now is None:
        now = datetime.datetime.now(tz=tz)

    # all 5min at weekend and night
    if now.weekday() >= 5 or now.hour < 7 or now.hour >= 22:
        return 5 * 60

    # otherwise, immediately between 7:55 and 10:50
    if datetime.time(hour=7, minute=55, tzinfo=tz) < now.time() < datetime.time(hour=10, minute=50, tzinfo=tz):
        # wait 10s if between more then 3min before and after full quarter hour
        if 3 <= now.minute % 15 < 12:
            return 10
        # otherwise, wait only 1s
        return 1

    # otherwise, 1 minute
    return 60


def keep_checking(checker: AppointmentChecker, selection_strategy: OfficeSelectionStrategy,
                  intention_strategy: IntentionSelectionStrategy, form_values: FormValues = form_values):
    while True:
        try:
            while not checker.check_citas_available(form_values, selection_strategy, intention_strategy):
                print_with_time("No appointment available")
                sleep(seconds_until_next_check())
            print_with_time("Appointments available")
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            traceback.print_exc()
        play_alarm_until_input()


def run_manual_mode(checker: AppointmentChecker, intention_strategy: IntentionSelectionStrategy,
                    form_values: FormValues = form_values):
    while True:
        checker.check_citas_available(form_values, ManualOfficeSelectionStrategy(), intention_strategy)
        input("Please press Enter to continue...")


def run_check_all_offices(checker: AppointmentChecker, intention_strategy: IntentionSelectionStrategy,
                          form_values: FormValues = form_values):
    dfs_strategy = DFSOfficeSelectionStrategy()
    try:
        while True:
            try:
                if checker.check_citas_available(form_values, dfs_strategy, intention_strategy):
                    appointments = list(scrape_appointments(checker.driver))
                    if appointments:
                        print(f"{dfs_strategy.last_province} – {dfs_strategy.last_office} has appointments:")
                        appointments.sort()
                        for appointment in appointments:
                            print("\t" + appointment.strftime("%a %Y-%m-%d %H:%M:%S"))
                        continue
                print(f"{dfs_strategy.last_province} – {dfs_strategy.last_office} has no appointments.")
                dfs_strategy.notify_about_no_appointments_for_last_selection()
            except DFSOfficeSelectionStrategy.NoMoreOfficesException:
                pass
            except NoSuchElementException:
                print(f"{dfs_strategy.last_province} has no proper NIE assignment option")
                dfs_strategy.notify_about_no_appointments_for_last_selection()
            sys.stdout.flush()
    except DFSOfficeSelectionStrategy.NoMoreProvincesException:
        pass


def run():
    try:
        checker = AppointmentChecker()

        parser = argparse.ArgumentParser(description="Check for available appointments at the Spanish government")

        intention_group = parser.add_mutually_exclusive_group(required=True)
        intention_group.add_argument("--nie", help="Check for appointments for a NIE assignment",
                                     dest="intention_strategy", action='store_const',
                                     const=find_assign_nie_option)
        intention_group.add_argument("--registration", help="Check for appointments for registration as EU citizen",
                                     dest="intention_strategy", action="store_const",
                                     const=find_register_eu_citizen_option)

        parser.add_argument("--slow", action="store_true", help="Wait a second before submitting a page")

        mode_parsers = parser.add_subparsers(required=True, dest="mode", title="mode")
        mode_parsers.add_parser("manual", help="Select offices manually") \
            .set_defaults(mode=lambda parsed_args: run_manual_mode(checker, parsed_args.intention_strategy))
        mode_parsers.add_parser("alloffices", help="List all appointments for all offices") \
            .set_defaults(mode=lambda parsed_args: run_check_all_offices(checker, parsed_args.intention_strategy))
        endless_parser = mode_parsers.add_parser("endless", help="Keep checking for appointments in an endless loop")
        endless_parser.set_defaults(mode=lambda parsed_args: keep_checking(checker,
                                                                           parsed_args.office_strategy(parsed_args),
                                                                           parsed_args.intention_strategy))
        office_parsers = endless_parser.add_subparsers(title="office selection mode",
                                                       required=True)
        office_parsers.add_parser("nearvalencia", help="The office in Valencia nearest to the city is chosen") \
            .set_defaults(office_strategy=lambda _: NearestValenciaOfficeSelectionStrategy())
        specific_office_parser = office_parsers.add_parser("specific", help="Choose a specific office")
        specific_office_parser.add_argument("province")
        specific_office_parser.add_argument("office")
        specific_office_parser.set_defaults(office_strategy=
                                            lambda parsed_args: SpecificOfficeSelectionStrategy(parsed_args.province,
                                                                                                parsed_args.office))

        args = parser.parse_args()
        checker.slow = args.slow
        args.mode(args)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    run()
