from collections import namedtuple
from datetime import datetime
import re

from openpyxl import load_workbook

import const
import exceptions


class Person:
    """A Person is a human being.
    .name: 
        Full name of the person e.g. "John Doe".
    .service: 
        Each shift needs a service 'verzorger' and a service 'algemeen'
        so we need to know wich type of service a person provides.
    .not on weekday: 
        The weekdays on which the person doesn't want to be scheduled.
    .not in shift: 
        The type of shift in which the person doesn't want to be scheduled.
    .shifts_per_weeks: 
        On how many shifts in how many weeks the person wants to be scheduled.
    .not_in_timespan: 
        On which days of the year quarter the person 
        doesn't want to be scheduled.
    .preferred_shifts:
        Some volunteers prefer to be scheduled on a specific day and shift.
    .availability_counter: 
        The number of times that the person 
        is available for scheduling per one or more weeks.
        The counter is initialised with shifts_per_week.shifts.
        The counter is reduced by 1 when a scheduling happens for the person.
        The counter is reset at the start of scheduling a new week 
        if the value is 0.
    .weekend_counter:
        Each person is obligated to run a shift in the weekend once a month.
        The counter has to be 4 for the person to be eligible for
        schediling in a weekend.
        When a person is scheduled in a weekend, the weekend_counter is
        reset to zero. At the start of scheduling a new week, 
        the counter is incremented by 1. While the counter is not yet 4,
        the person is not available for scheduling in the weekend.
    """
    def __init__(self):
        self.name = "" 
        self.service = ""  # 'algemeen' or 'verzorger'  
        self.shifts_per_weeks = ()  # namedtuple ShiftsPerWeeks
        self.not_on_shifts_per_weekday = dict()
        self.not_in_timespan = ()
        self.preferred_shifts = dict()
        self.availability_counter = 0 
        self.weekend_counter = 4

    def __repr__(self):
        return (
            f'{self.name}, '
            f'{self.service:10}, '
            f'shifts_per_weeks: {tuple(self.shifts_per_weeks)}, '
            f'not_on_shifts_per_weekday: {self.not_on_shifts_per_weekday}, '
            f'not_in_timespan: {self.not_in_timespan}, '
            f'preferred_shifts: {self.preferred_shifts}, '
            f'availability_counter: {self.availability_counter}, '
            f'weekend_counter: {self.weekend_counter}'
        )


class Volunteers:
    """Volunteers is a collection of instances Person who work without
    fee for a hospice organisation.
    
    .generalist_names:
        A set of person names who's service is generic.
    .caretaker_names:
        A set of person names who's service is caretaking.
    """
    def __init__(self, sourcefilename):

        self.sourcefilename = sourcefilename
        print(f'\nBestand lezen: "{self.sourcefilename}"...\n')

        # self.persons is a tuple with instances of class 'Person'
        self.persons = self._read_volunteersfile(self.sourcefilename)
        self._check_sanity("duplicate_names")

        # Get all 'generic' workers and all 'caretaker' workers.
        # Note: we use set operators on these groups and
        # the set operator 'difference' doesn't work on lists.
        # So we convert the list to a tuple and then to a set.
        self.generalist_names = set(tuple([
                p.name
                for p in self.persons
                if p.service == 'algemeen']))
        self.caretaker_names = set(tuple([ 
                p.name
                for p in self.persons
                if p.service == 'verzorger' 
            ]))

    def find(self, namelist):
        """Return all found persons 
        in the Volunteers collection in namelist.
        """
        result = []
        for name in namelist:
            for person in self.persons:
                if person.name == name:
                    result.append(person)
        return result
    
    def show_count(self):
        print()
        print(f'Er zijn {len(self.caretaker_names)} verzorgers beschikbaar.')
        print(f'Er zijn {len(self.generalist_names)} algemenen beschikbaar.')
        print()

    def show_data(self):
        print()
        for p in self.persons:
            print(p)

    def day_and_shifts_to_dict(self,
            day_and_shifts_string, columnname, line_num):
        """The day_and_shifts_string is 
        for example 'ma:1, 2,3,4#  wo:3,4 # zo:4.'
        The function returns the dict: { 1: (1,2,3,4), 3: (3,4), 7: (4) }
        The weekddays are translated to isoweekday numbers,
        and the shifts are in a tuple.
        """
        if day_and_shifts_string:
            spaceless_string = day_and_shifts_string.replace(" ", "")
            
            # Check the input string
            self._check_sanity('day_and_shifts_string', spaceless_string,
                columnname=columnname, line_num=line_num)
            
            # Remove the last '#' AFTER the sanity check
            spaceless_string = spaceless_string.strip('#')
            
            # Make a list of items in the string 
            # with delimiter = '#':
            day_and_shifts_items = (i for i in spaceless_string.split('#'))
            # day_and_shift_list is e.g. ['ma:1,2,3,4', 'wo:3,4', 'zo:4'] 
            result_dict = {}
            for item in day_and_shifts_items:
                sep_weekday_and_shift = item.split(":")
                # The first sep_weekday_and_shift is ['ma', '1,2,3,4']
                # Now make a dict with key = isoweekday number
                # and value = tuple of shifts.
                key = const.WEEKDAY_LOOKUP[sep_weekday_and_shift[0]] 
                value = (int(i) for i in sep_weekday_and_shift[1].split(","))
                result_dict[key] = tuple(value)
            return result_dict
        else:
            return {}

    def _read_volunteersfile(self, infile):
        """read a prepared xls file <infile>.
        The attributes are extracted from the column names.
        Read the values from the xls file.
        Assign the values to the an instance of class 'Person'.
        Return a list of the instances 'Person'.
        """
        volunteers = []
        ShiftsPerWeeks = namedtuple('ShiftsPerWeeks', ['shifts', 'per_weeks'])
        
        wb = load_workbook(filename=infile, data_only=True)
        ws = wb.active
        reader = ws.iter_rows(min_col=10, values_only=True)

        # get names from column headers
        # TODO kolomnamen kunnen geen spaties of '-' teken bevatten?
        # TODO controle of wel wel headers zijn
        Data = namedtuple("Data", next(reader))
        # start enumerating with line number 2
        for line_num, xls_data in enumerate(map(Data._make, reader), 2):
            try:
                # read only the Active persons
                if (xls_data.Actief):

                    # Column Service
                    # TODO Iemand kan zowel verzorger als algemeen zijn!!
                    # Moet dus een list worden i.p.v. string, 
                    # met test op 'in' i.p.v. ==
                    service = xls_data.Service or ""
                    service = service.strip()
                    self._check_sanity("service", service, "Service", line_num)

                    # Columns Achternaam, Tussenv, Voornaam
                    # Person name
                    insert = xls_data.Tussenv or ""
                    if insert.strip():
                        pass
                    if insert.strip():
                        insert = " " + insert
                    givenname = xls_data.Voornaam or ""
                    surname = xls_data.Achternaam or "" 
                    name = (givenname.strip() + insert + " " + surname.strip())

                    # Column NietOpDagEnDienst
                    not_on_shifts_per_weekday = (
                        xls_data.NietOpDagEnDienst or "")
                    not_on_shifts_per_weekday = (
                        self.day_and_shifts_to_dict(not_on_shifts_per_weekday,
                        'NietOpDagEnDienst', line_num))
                    
                    # Column VoorkeurDagEnDienst
                    # preferred_shifts (prefs)
                    preferred_shifts = xls_data.VoorkeurDagEnDienst or ""
                    prefs_dict = (
                        self.day_and_shifts_to_dict(preferred_shifts,
                        'VoorkeurDagEnDienst', line_num)
                        )
                    
                    # Column DienstenPerAantalWeken
                    # shifts_per_weeks namedtuple
                    # xls OpenOffice is confusing. Even though the column
                    # is formatted as text, the value 1,1 is read as 
                    # a float! After entering the value *again*
                    # it is read as a string.
                    shifts_per_week = xls_data.DienstenPerAantalWeken or ""
                    shifts_per_week = shifts_per_week.replace(" ", "")
                    self._check_sanity("shifts_per_weeks", 
                            shifts_per_week, "DienstenPerAantalWeken",
                            line_num)
                    shifts_per_week = (shifts_per_week.split(","))
                    # Make namedtuple
                    shifts_per_weeks = ShiftsPerWeeks._make(
                            [int(shifts_per_week[0]), 
                             int(shifts_per_week[1])])

                    # availability_counter (no column)
                    availability_counter = shifts_per_weeks.shifts
                    
                    # weekend counter (no column)
                    # Initially everybody is available for weekends
                    weekend_counter = const.WEEKENDCOUNTER

                    # Column NietInPeriode
                    not_in_timespan_value = xls_data.NietInPeriode or ""
                    not_in_timespan = tuple( 
                        period for period in
                        not_in_timespan_value.replace(" ", "").split(",") 
                    )
                    self._check_sanity('dates_string', 
                        not_in_timespan, 'NietInPeriode', line_num)

                    # Now we have all the data to instantiate a Person
                    person = Person()
                    person.name = name
                    person.service = service
                    person.not_on_shifts_per_weekday = (
                        not_on_shifts_per_weekday)
                    person.shifts_per_weeks = shifts_per_weeks
                    person.not_in_timespan = not_in_timespan
                    person.preferred_shifts = prefs_dict
                    person.availability_counter = availability_counter
                    person.weekend_counter = weekend_counter
                    volunteers.append(person)
            # TODO The value error still comes 
            # from namedtuple("data", next(reader))!
            # reraise??
            except exceptions.InvalidColumnHeaderError:
                exit()
        return tuple(volunteers)

    def _check_sanity(self, test, operand=None, 
                      columnname=None, line_num=None):
        """Check the validity of the input data from the sourcefile.
        """
        # ------------------------------------------------------------
        # Start of helper functions
        def find_duplicate_personnames(nameslist, name):
            return [idx for idx, value in enumerate(nameslist)
                    if value == name]
        
        def check_day_and_shifts_string(operand):
            # Return None if something is wrong.
            # return anything else if things are o.k.

            # There are no spaces in the operand.
            # operand example: di:1,2,3#wo:1,2,3#do:1,2,3#vr:1,2,3#
            
            # Check if the operand ends with a '#'.
            if operand[-1] != "#":
                return None

            # The pattern is
            # weekday + ':'
            #   + comma seperated shiftnumber e.g (1,2,3,4) or (1,2) or (3)
            # and then an endless repetition of
            #   '#' + (the first part, ending with '#').
            # Example: ma:1,2,3,4# di:1,2,3# zo:4#
            # TODO 2,2,3 should not match!
            pattern = re.compile(
                r'^(((ma|di|wo|do|vr|za|zo)[:][1-4]([,][1-4])*)[#])*$')
            return re.match(pattern, operand)

        def check_shifts_per_weeks(operand):
            # shifts_per_weeks must be like 1,2 or 3,2 or ...
            pattern = re.compile(r'^(1,1|1,2|3,2|2,1|2,3)$')
            return re.match(pattern, operand)

        # End of helper functions
        # ------------------------------------------------------------
        if test == 'duplicate_names': 
            nameslist = [p.name for p in self.persons]
            for name in nameslist:
                if len(find_duplicate_personnames(nameslist, name)) > 1:
                    raise exceptions.DuplicatePersonnameError(name)
        
        if test == 'day_and_shifts_string':
            if not check_day_and_shifts_string(operand):
                raise exceptions.DayAndShiftsStringError(
                    f'kolom: {columnname!r}, '
                    f'regel: {line_num}, '
                    f'tekst: {operand!r})')
        
        if test == "shifts_per_weeks":
            if not check_shifts_per_weeks(operand):
                raise exceptions.ShiftsPerWeeksError(
                    f'kolom: {columnname!r}, '
                    f'regel: {line_num}, '
                    f'tekst: {operand!r})')
        
        if test == "service":
            if (not operand) or operand not in ('verzorger, algemeen'):
                raise exceptions.ServicenameError(
                    f'kolom: {columnname!r}, '
                    f'regel: {line_num}, '
                    f'tekst: {operand!r})')

        if test == "dates_string" and all(operand):
            # TODO gekopieerd uit init_agenda!
            # TODO hat jaar kan ook onjuist zijn, maar denk eraan
            # dat de kwartalen over het jaar heen gaan.
            for item in operand:
                dates = item.split('>') 
                try:
                    if len(dates) > 1:
                        startdate = datetime.strptime(dates[0], 
                                    const.DATEFORMAT).date()
                        enddate = datetime.strptime(dates[1], 
                                  const.DATEFORMAT).date()
                        if enddate < startdate:
                            raise exceptions.DateTimespanError(
                                f'kolom: {columnname!r}, '
                                f'regel: {line_num}, '
                                f'tekst: {item!r})')
                    else:
                        # The variable is not important, just the execution
                        # of the function.
                        _ = datetime.strptime(dates[0], 
                            const.DATEFORMAT).date()
                except ValueError:
                    line_num = str(line_num)
                    raise exceptions.DateFormatError(
                        f'kolom: {columnname!r}, '
                        f'regel: {line_num}, '
                        f'tekst: {item!r})')


if __name__ == '__main__':
    xls_filename = 'vrijwilligers-2023-kw2.xlsx'
    group = Volunteers(xls_filename)
    # group.show_data()
    group.show_count()
