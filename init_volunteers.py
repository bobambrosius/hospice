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
        self.availability_counter = 0 

    def __repr__(self):
        return(
            f'name: {self.name}, '
            f'service: { self.service }, '
            f'not_on_shifts_per_weekday: {self.not_on_shifts_per_weekday}, '
            f'shifts_per_weeks: {self.shifts_per_weeks}, '
            f'not_in_timespan: {self.not_in_timespan}, '
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
                        # not_on_shifts_per_weekday (nospw)
                        nospw_dict = {} 
                        if csv_data.NietOpDienstPerWeekdag:
                            # The csv_data is e.g. 
                            #   'ma:1, 2,3,4#  wo:3,4 # zo:4  '
                            nospw = csv_data.NietOpDienstPerWeekdag.replace(" ","")
                            # Make a list of items in the string 
                            # with delimiter = '#':
                            nospw_base = [ i for i in nospw.split('#') ]
                            #TODO last char cannot be a '#'. 
                            #       Need defensive programming!!
                            #nospw_base is now 
                            #       ['ma:1,2,3,4', 'wo:3,4', 'zo:4'] 
                            for item in nospw_base:
                                nospw_weekday = item.split(":")
                                # The first nospw_weekday is ['ma', '1,2,3,4']
                                # Now make an integer list of the 
                                # shifts string, and replace the weekday names 
                                # with isoweekday numbers.
                                nospw_dict[ 
                                    const.WEEKDAY_LOOKUP[nospw_weekday[0]] ] = [ 
                                    int(i) for i in nospw_weekday[1].split(",") ]
                            # Before weekday_lookup the nospw_dict endresult is
                            #       { 'ma': [1,2,3,4], 'wo': [3,4], 'zo'; [4] }
                            # After weekday_lookup the nospw_dict endresult is 
                            #       { 1: [1,2,3,4], 3: [3,4], 7: [4] }

                        # Column DienstenPerAantalWeken
                        # shifts_per_weeks dicionary
                        shifts_per_week = (
                            csv_data.DienstenPerAantalWeken.replace(" ","").split(","))
                        shifts_per_weeks = {
                            "shiftcount": int( shifts_per_week[0].strip() ), 
                            "per_weeks": int( shifts_per_week[1].strip() ) }

                        # availability_counter (no column)
                        availability_counter = shifts_per_weeks["shiftcount"]

                        # Column NietInPeriode
                        not_in_timespan = []
                        if csv_data.NietInPeriode:
                            for period in csv_data.NietInPeriode.replace(" ","").split(","):
                                not_in_timespan.append(period.strip())

                        person = Person()
                        person.name = name
                        person.service = service
                        person.not_on_shifts_per_weekday = nospw_dict
                        person.shifts_per_weeks = shifts_per_weeks
                        person.not_in_timespan = not_in_timespan
                        person.availability_counter = availability_counter
                        volunteers.append(person)
                except AttributeError as e:
                    print(e)
                    exit()
        return volunteers


if __name__ == '__main__':
    csv_filename = 'vrijwilligers-2023-kw2.csv'
    group = Volunteers(csv_filename)
    #group.show_volunteers_data()
    group.show_volunteerscount()
