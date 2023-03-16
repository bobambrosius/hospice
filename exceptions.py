import sys

# Don't print Traceback
#sys.tracebacklimit = 0

class DateTimespanError(Exception):
    """Exception raised if in two dates, the second date 
    is smaller than the first.
    """

class DateFormatError(Exception):
    """Exception raised if the format of a date 
    doesn't conform to const.py.
    """

class DuplicatePersonnameError(Exception):
    """Exception raised if the sourcefile contains duplicate names.
    """

class ServicenameError(Exception):
    """Exception raised if service has wrong name.
    """

class ShiftsPerWeeksError(Exception):
    """Exception raised if shifts_per_weeks has wrong format.
    """

class DayAndShiftsStringError(Exception):
    """Exception raised if the day_and_shifts_string has the wrong format.

    Attributes:
        inputstring -- day_and_shifts_string with wrong format.
    """
    def __init__(self, inputstring, msg=(
            f'formaat niet correct in kolom ')
            ):
        self.name = inputstring
        self.msg = msg
        super().__init__(self.msg + inputstring + '"')


class InvalidColumnHeaderError(ValueError):
    """Exception raised if a columnheader in the sourcefile is not valid.

    Attributes:
        Columnheader -- columnheader with invalid name
    """
    def __init__(self, columnheader, msg=(
            f'Kolomkop heeft een '
            f'ongeldige waarde. \n'
            f'Alleen alfabet teken en '
            f'underscore is toegestaan.')
            ):
        self.name = columnheader
        self.msg = msg
        super().__init__(self.msg + ': "' + columnheader + '"')


class InvalidSourceFileError(Exception):
    """Exception raised if the sourcefile can't be read.
    """

