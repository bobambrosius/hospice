from collections import namedtuple
import csv
import const


class Person:
    """
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
        The counter is initialised with shifts_per_week['shiftcount'].
        The counter is reduced by 1 when a scheduling happens for the person.
        The counter is reset at the start of scheduling a new week 
        if the value is 0.
    """

    def __init__(self):
        self.name = "" 
        self.service = "" 
        self.not_on_shifts_per_weekday = dict()
        self.shifts_per_weeks = dict()
        self.not_in_timespan = [] 
        self.preferred_shifts = dict()
        self.availability_counter = 0 

    def __repr__(self):
        return(
            f'name: {self.name}, '
            f'service: { self.service }, '
            f'not_on_shifts_per_weekday: {self.not_on_shifts_per_weekday}, '
            f'shifts_per_weeks: {self.shifts_per_weeks}, '
            f'not_in_timespan: {self.not_in_timespan}, '
            f'preferred_shifts: {self.preferred_shifts}, '
            f'availability_counter: {self.availability_counter}')


class Volunteers:
    def __init__(self, volunteerfilename):
        self.volunteerfilename = volunteerfilename
        print(f'Bestand lezen: "{self.volunteerfilename}"...')

        # self.persons is a list op namedtuples 'Person'
        self.persons = self._get_volunteers(self.volunteerfilename)

        # Get all 'generic' workers and all 'caretaker' workers.
        # Note: we use set operators on these groups and
        # the set operator 'difference' doesn't work on lists.
        # So we convert the list to a tuple and then to a set.
        #gg = set( tuple([
        #        p.name 
        #        for p in self.persons 
        #        if p.service == 'algemeen']) )
        self.group_generic = set(tuple( [
                p.name
                for p in self.persons
                if p.service == 'algemeen'
            ]))
        self.group_caretaker = set(tuple([ 
                p.name
                for p in self.persons
                if p.service == 'verzorger'
            ]))

    def find(self, namelist):
        """Return all instances of Volunteer in namelist.
        """
        result = []
        for name in namelist:
            for person in self.persons:
                if person.name == name:
                    result.append(person)
        return result

    def show_volunteerscount(self):
        print()
        print(f'Er zijn {len(self.group_caretaker)} verzorgers beschikbaar.')
        print(f'Er zijn {len(self.group_generic)} algemenen beschikbaar.')

    def show_volunteers_data(self):
        print()
        for p in self.persons:
            print(p)

    def day_and_shift_to_dict(self, day_and_shift_string):
        """
        The day_and_shift_string is like 'ma:1, 2,3,4#  wo:3,4 # zo:4.'
        The function returns the dict: { 1: [1,2,3,4], 3: [3,4], 7: [4] }
        The days are translated to isoweekday numbers,
        and the shifts are in a tuple.
        """
        result_dict = {}
        if day_and_shift_string:
            spaceless_string = day_and_shift_string.replace(" ","")
            # Make a list of items in the string 
            # with delimiter = '#':
            day_and_shift_list = [ i for i in spaceless_string.split('#') ]
            #TODO last char cannot be a '#'. 
            #       Need defensive programming!!
            # day_and_shift_list is e.g. ['ma:1,2,3,4', 'wo:3,4', 'zo:4'] 
            for item in day_and_shift_list:
                sep_weekday_and_shift = item.split(":")
                # The first sep_weekday_and_shift is ['ma', '1,2,3,4']
                # Now make a dict with key = isoweekday number
                # and value = list of shifts.
                key = const.WEEKDAY_LOOKUP[sep_weekday_and_shift[0]] 
                value = ( int(i) for i in sep_weekday_and_shift[1].split(",") )
                result_dict[key] = list(value)

        # Result_dict is e.g. { 1: (1,2,3,4), 3: (3,4), 7: (4) }
        return result_dict

    def _get_volunteers(self, infile):
        """read a prepared csv file <infile>, which is record-delimited with
        DELIMITER, into a dynamic namedtuple.
        The attributes are extracted from the column names.
        Read the values from the csv file.
        Assign the values to the an instance of class 'Person'.
        Return a list of the instances 'Person'.
        """
        volunteers = []
        with open(infile, newline="") as f:
            #TODO check that the DELIMITER value is not used in the cells
            reader = csv.reader(f, delimiter=const.CSV_DELIMITER)
            # get names from column headers
            #TODO kolomnamen kunnen geen spaties of '-' teken bevatten
            #TODO Er mogen niet twee of meer personen met dezelfde naam zijn.
            Data = namedtuple("Data", next(reader))
            for csv_data in map(Data._make, reader):
                try:
                    # read only the persons with a particular service 
                    if ( (csv_data.Service == 'algemeen' 
                            or csv_data.Service == 'verzorger') 
                            and csv_data.DienstenPerAantalWeken ):

                        # Column Service
                        service = csv_data.Service

                        # Columns Achternaam, Tussenv, Voornaam
                        # Person name
                        tussenvoegsel = ""
                        if csv_data.Tussenv: 
                            tussenvoegsel = " " + csv_data.Tussenv
                        name = (csv_data.Voornaam 
                            + tussenvoegsel + " " + csv_data.Achternaam)

                        # Column NietOpDienstPerWeekdag
                        not_on_shifts_per_weekday = (
                            self.day_and_shift_to_dict(
                                csv_data.NietOpDienstPerWeekdag) 
                            )
                        
                        # Column VoorkeurDagEnDienst
                        # preferred_shifts (prefs)
                        prefs_dict = (
                            self.day_and_shift_to_dict(
                                csv_data.VoorkeurDagEnDienst)
                            )
                        
                        # Column DienstenPerAantalWeken
                        # shifts_per_weeks dicionary
                        shifts_per_week = (
                            csv_data.DienstenPerAantalWeken.replace(" ","").split(","))
                        shifts_per_weeks = {
                            "shiftcount": int( shifts_per_week[0].strip() ), 
                            "per_weeks": int( shifts_per_week[1].strip() ) 
                            }

                        # availability_counter (no column)
                        availability_counter = shifts_per_weeks["shiftcount"]

                        # Column NietInPeriode
                        not_in_timespan = []
                        if csv_data.NietInPeriode:
                            for period in csv_data.NietInPeriode.replace(" ","").split(","):
                                not_in_timespan.append(period)

                        # Now we have all the data 
                        # to make an instance of class Person
                        person = Person()
                        person.name = name
                        person.service = service
                        person.not_on_shifts_per_weekday = (
                            not_on_shifts_per_weekday)
                        person.shifts_per_weeks = shifts_per_weeks
                        person.not_in_timespan = not_in_timespan
                        person.preferred_shifts = prefs_dict
                        person.availability_counter = availability_counter
                        volunteers.append(person)
                except AttributeError as e:
                    print(e)
                    exit()
        return volunteers


if __name__ == '__main__':
    csv_filename = 'vrijwilligers-2023-kw2.csv'
    group = Volunteers(csv_filename)
    group.show_volunteers_data()
    group.show_volunteerscount()
