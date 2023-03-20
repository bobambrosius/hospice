import sys

# Maximum levels of Traceback. 0 = off
sys.tracebacklimit = 6


class SourcefileValueError(Exception):
    """General module error
    """
    def __init__(self, columnname, line_num, operand):
        self.columnname = columnname
        self.line_num = line_num
        self.operand = operand
        super().__init__(
            f'Formaat niet correct in '
            f'kolom: {self.columnname!r}, '
            f'regel: {self.line_num}, '
            f'tekst: {self.operand!r}')
    
    
class DateTimespanError(SourcefileValueError):
    """Exception raised if in two dates, the second date
    is smaller than the first.
    """
    def __init__(self, columnname, line_num, operand):
        super().__init__(columnname, line_num, operand)


class DateFormatError(SourcefileValueError):
    """Exception raised if the format of a date
    doesn't conform to const.py.
    """
    def __init__(self, columnname, line_num, operand):
        super().__init__(columnname, line_num, operand)


class ServicenameError(SourcefileValueError):
    """Exception raised if service has wrong name.
    """
    def __init__(self, columnname, line_num, operand):
        super().__init__(columnname, line_num, operand)


class ShiftsPerWeeksError(SourcefileValueError):
    """Exception raised if shifts_per_weeks has wrong format.
    """
    def __init__(self, columnname, line_num, operand):
        super().__init__(columnname, line_num, operand)


class DayAndShiftsStringError(SourcefileValueError):
    """Exception raised if the day_and_shifts_string has the wrong format.
    """
    def __init__(self, columnname, line_num, operand):
        super().__init__(columnname, line_num, operand)


class SourceFileHeaderError(Exception):
    """Exception raised if a header is not in allowed headers.
    """


class DuplicatePersonnameError(Exception):
    """Exception raised if the sourcefile contains duplicate names.
    """


class InvalidSourceFileError(Exception):
    """Exception raised if the sourcefile can't be read.
    """


class MissingCaseValueError(RuntimeError):
    """Statement 'Case' cold not intepret value
    """
