# niescraper

Controls your browser in order to search for and book appointments at the Spanish Extranjería.

## Installation

To install the tool, run `pip install .` in the root directory. If you plan to edit files, run `pip install -e .` instead.

Firefox needs to be installed as well. It should be easy to support multiple browsers, but so far I had no reason to do it.

## Usage

### Entering personal information

Parsing the personal information from the CLI is not yet implemented. Open [app.py](./niescraper/app.py) and put your data into the `form_values` dictionary.

### Command line parameters

You can get an overview over the supported command line parameters using `niescraper --help`.

Currently, only appointments for the registration as a residing EU citizen (`--registration`) and for requesting a NIE number (`--nie`) are supported.

You can choose between three modes:
- `manual`: You have to select an office manually in the browser. The tool will do the rest and check if there is an appointment available in this office.
- `alloffices`: All offices are checked for appointments once and the results are printed.
- `endless`: A single office is checked frequently and an alarm sound is played once an appointment is available or an exception occurs.
  The time interval between two checks depends on the current time.

For example, to frequently check for registration appointments at the Extranjería Bailen in Valencia, run 
``niescraper --registration endless specific Valencia Bailen``.