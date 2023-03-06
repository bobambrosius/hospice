class DuplicatePersonnameError(Exception):
    """Exception raised if the sourcefile contains duplicate names.

    Attributes:
        name -- personname that is a duplicate
    """
    def __init__(self, name, msg='Naam komt dubbel voor'):
        self.name = name
        self.msg = msg
        super().__init__(self.msg + ': "' + name + '"')


class DayAndShiftsStringError(Exception):
    """Exception raised if the day_and_shifts_string has the wrong format.

    Attributes:
        inputstring -- day_end_shifts_string with wrong format.
    """
    def __init__(self, inputstring, msg=(
            f'formaat van dag-en-diensten niet correct in kolom ')
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
