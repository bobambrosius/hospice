import sys

# Maximum levels of Traceback. 0 = off
sys.tracebacklimit = 2


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
    def __init__(self, columnname, line_num, operand):
        self.columnname = columnname
        self.line_num = line_num
        self.operand = operand
        super().__init__(
            f'Formaat niet correct in '
            f'kolom: {self.columnname!r}, '
            f'regel: {self.line_num}, '
            f'tekst: {self.operand!r})')


class InvalidSourceFileError(Exception):
    """Exception raised if the sourcefile can't be read.
    """
