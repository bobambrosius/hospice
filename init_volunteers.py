from collections import namedtuple
import re
import traceback
import csv
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
    .avlblty_counter: 
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
        self.service = "" 
        self.shifts_per_weeks = "" # namedtuple ShiftsPerWeeks
        self.not_on_shifts_per_weekday = dict()
        self.not_in_timespan = [] # a tuple after reading data
        self.preferred_shifts = dict()
        self.avlblty_counter = 0 
        self.weekend_counter = 4

    def __repr__(self):
        return(
            f'name: {self.name}, '
            f'service: { self.service }, '
            f'shifts_per_weeks: ({self.shifts_per_weeks.shifts},'
            f'{self.shifts_per_weeks.per_weeks}), '
            f'not_on_shifts_per_weekday: {self.not_on_shifts_per_weekday}, '
            f'not_in_timespan: {self.not_in_timespan}, '
            f'preferred_shifts: {self.preferred_shifts}, '
            f'avlblty_counter: {self.avlblty_counter}, '
            f'weekend_counter: {self.weekend_counter}'
        )


class Volunteers:
    """Volunteers is a collection of instances Person who work without
    fee for a hospice organisation.
    
    .generalist_names:
        A set of person names who's service is generic.
    .caretaker_names:
        A set of person names who's service is caretaking."""
    
    def __init__(self, sourcefilename):

        self.sourcefilename = sourcefilename
        print(f'Bestand lezen: "{self.sourcefilename}"...')

        # self.persons is a tuple with instances of class 'Person'
        self.persons = self._get_volunteers(self.sourcefilename)
        self._check_sanity("duplicate_names")

        # Get all 'generic' workers and all 'caretaker' workers.
        # Note: we use set operators on these groups and
        # the set operator 'difference' doesn't work on lists.
        # So we convert the list to a tuple and then to a set.
        #gg = set( tuple([
        #        p.name 
        #        for p in self.persons 
        #        if p.service == 'algemeen']) )
        self.generalist_names = set(tuple( [
                p.name
                for p in self.persons
                if p.service == 'algemeen'
            ]))
        self.caretaker_names = set(tuple([ 
                p.name
                for p in self.persons
                if p.service == 'verzorger' 
            ]))

    def find(self, namelist):
        """Return all found persons in the Volunteers collection in namelist."""
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

    def day_and_shifts_to_dict(self, day_and_shifts_string, columnname, line_num):
        """The day_and_shifts_string is for example 'ma:1, 2,3,4#  wo:3,4 # zo:4.'
        The function returns the dict: { 1: (1,2,3,4), 3: (3,4), 7: (4) }
        The weekddays are translated to isoweekday numbers,
        and the shifts are in a tuple."""

        if day_and_shifts_string:
            spaceless_string = day_and_shifts_string.replace(" ","")
            
            # Check the input string
            self._check_sanity('day_and_shifts_string', spaceless_string,
                columnname = columnname, line_num = line_num)
            
            # Remove the last '#' AFTER the sanity check
            spaceless_string = spaceless_string.strip('#')
            
            # Make a list of items in the string 
            # with delimiter = '#':
            day_and_shifts_items = ( i for i in spaceless_string.split('#') )
            # day_and_shift_list is e.g. ['ma:1,2,3,4', 'wo:3,4', 'zo:4'] 
            result_dict = {}
            for item in day_and_shifts_items:
                sep_weekday_and_shift = item.split(":")
                # The first sep_weekday_and_shift is ['ma', '1,2,3,4']
                # Now make a dict with key = isoweekday number
                # and value = tuple of shifts.
                key = const.WEEKDAY_LOOKUP[sep_weekday_and_shift[0]] 
                value = ( int(i) for i in sep_weekday_and_shift[1].split(",") )
                result_dict[key] = tuple(value)
            return result_dict
        else:
            return {}

    def _get_volunteers(self, infile):
        """read a prepared csv file <infile>, which is record-delimited with
        DELIMITER, into a dynamic namedtuple.
        The attributes are extracted from the column names.
        Read the values from the csv file.
        Assign the values to the an instance of class 'Person'.
        Return a list of the instances 'Person'."""
        
        # Peform some basic tests to validate the sourcefile.
        with open(infile, newline="") as f:
            dialect = csv.Sniffer().sniff(f.read(40))
            if dialect.delimiter != const.CSV_DELIMITER:
                raise exceptions.InvalidSourceFile('Het veld-scheidingteken is niet ";".')
            f.seek(0)
            if not csv.Sniffer().has_header(f.read(40)):
                raise exceptions.InvalidSourceFile('Kolomkoppen ontbreken.')
            f.seek(0)

        volunteers = []
        ShiftsPerWeeks = namedtuple('ShiftsPerWeeks', 'shifts per_weeks')
        with open(infile, newline="") as f:
            #TODO check that the DELIMITER value is not used in the cells
            reader = csv.reader(f, delimiter=const.CSV_DELIMITER)
            # get names from column headers
            #TODO kolomnamen kunnen geen spaties of '-' teken bevatten
            Data = namedtuple("Data", next(reader))
            for csv_data in map(Data._make, reader):
                try:
                    # read only the persons with a particular service 
                    if ( (csv_data.Service == 'algemeen' 
                            or csv_data.Service == 'verzorger') 
                            and csv_data.DienstenPerAantalWeken ):

                        # Column Service
                        service = csv_data.Service.strip()

                        # Columns Achternaam, Tussenv, Voornaam
                        # Person name
                        tussenvoegsel = ""
                        if csv_data.Tussenv.strip(): 
                            tussenvoegsel = " " + csv_data.Tussenv.strip()
                        name = (csv_data.Voornaam.strip()
                            + tussenvoegsel + " " 
                            + csv_data.Achternaam.strip())

                        # Column NietOpDagEnDienst
                        not_on_shifts_per_weekday = (
                            self.day_and_shifts_to_dict(
                            csv_data.NietOpDagEnDienst,
                            'NietOpDagEnDienst', reader.line_num) 
                            )
                        
                        # Column VoorkeurDagEnDienst
                        # preferred_shifts (prefs)
                        # Add text in column VoorkeurStatisch.
                        prefs_dict = (
                            self.day_and_shifts_to_dict(
                            csv_data.VoorkeurDagEnDienst + csv_data.VoorkeurStatisch,
                            'VoorkeurDagEnDienst', reader.line_num)
                            )
                        
                        # Column DienstenPerAantalWeken
                        # shifts_per_weeks namedtuple
                        shifts_per_week = (
                            csv_data.DienstenPerAantalWeken.replace(" ","").split(","))
                        shifts_per_weeks = ShiftsPerWeeks(
                                int( shifts_per_week[0] ),
                                int( shifts_per_week[1] ))

                        # avlblty_counter (no column)
                        avlblty_counter = shifts_per_weeks.shifts
                        
                        # weekend counter (no column)
                        # Initially everybody is available for weekends
                        weekend_counter = 4

                        # Column NietInPeriode
                        not_in_timespan = []
                        if csv_data.NietInPeriode:
                            for period in csv_data.NietInPeriode.replace(" ","").split(","):
                                not_in_timespan.append(period)
                            # Make the data immutable
                            not_in_timespan = tuple(not_in_timespan)

                        # Now we have all the data to instantiate a Person
                        person = Person()
                        person.name = name
                        person.service = service
                        person.not_on_shifts_per_weekday = (
                            not_on_shifts_per_weekday)
                        person.shifts_per_weeks = shifts_per_weeks
                        person.not_in_timespan = not_in_timespan
                        person.preferred_shifts = prefs_dict
                        person.avlblty_counter = avlblty_counter
                        person.weekend_counter = weekend_counter
                        volunteers.append(person)
                #TODO The value error still comes 
                # from namedtuple("data", next(reader))!
                # reraise??
                except exceptions.InvalidColumnHeaderError:
                    exit()
        return tuple(volunteers)

    def _check_sanity(self, test, operand = None, 
                      columnname = None, line_num = None):
        """Check the validity of the input data."""
        
        #------------------------------------------------------------
        # Start of helper functions
        def find_duplicate_personnames(nameslist, name):
            return [ idx for idx, value in enumerate(nameslist)
                     if value == name ]
        
        def check_day_and_shifts_string(operand):
            # Return None if something is wrong.
            # return anything else if things are o.k.

            # There are no spaces in the operand.
            # operand example: di:1,2,3#wo:1,2,3#do:1,2,3#vr:1,2,3#
            
            # The operand does not end with a '#'.
            if operand[-1] != "#":
                return None

            # The pattern is
            # weekday + ':'
            #   + comma seperated shiftnumber e.g (1,2,3,4) or (1,2) or (3)
            # and then an endless repetition of
            #   '#' + (the first part, ending with '#').
            #TODO 2,2,3 should not match!
            pattern = re.compile(r'^(((ma|di|wo|do|vr|za|zo)[:][1234]([,][1234])*)[#])*$')
            return re.match(pattern, operand)

        # End of helper functions
        #------------------------------------------------------------
        if test == 'duplicate_names': 
            nameslist = [ p.name for p in self.persons ]
            for name in nameslist:
                if len(find_duplicate_personnames(nameslist, name)) > 1:
                    raise exceptions.DuplicatePersonnameError(name)
        
        if test == 'day_and_shifts_string':
            if not check_day_and_shifts_string(operand):
                raise exceptions.DayAndShiftsStringError(
                        columnname + ", regel: " 
                        + str(line_num) + ", tekst: " + operand)

if __name__ == '__main__':
    csv_filename = 'vrijwilligers-2023-kw2.csv'
    group = Volunteers(csv_filename)
    group.show_data()
    group.show_count()
