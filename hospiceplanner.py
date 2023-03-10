import csv
from datetime import datetime
from datetime import timedelta
import locale
from ordered_set import OrderedSet
from pathlib import Path
import random
import argparse
import textwrap
import init_agenda
import init_volunteers
import const
import holyday


class Scheduler:
    """Class Scheduler does only one thing.
    It schedules volunteers in a prepared agenda:
    2 persons on each of the 4 shifs per day.
    One person is a caretaker and the other one is 'general' 
    i.e. not a specialist.
    Scheduler has to account for personal wishes 
    like no being available on a specific weekday.
    Oh, and it can write the schedule to a csv file.
    """

    def __init__(self, year, quarter, version, agenda, volunteers):

        # Show month- and weeknames in Dutch
        # in agenda.csv file.
        locale.setlocale(locale.LC_TIME, "nl_NL.utf8")

        self.year = year
        self.quarter = quarter
        self.version = version
        self.agenda = agenda
        
        self.Volunteers = volunteers
        self.all_persons = volunteers.persons 

        # Prepare the agenda with personal wishes,
        # en register the availability in each agenda item .
        self._apply_static_rules() 

        self.generalist_names = volunteers.generalist_names
        self.caretaker_names = volunteers.caretaker_names
        # first weeknr of the year quarter
        self.currentweek = self.agenda.items[0].weeknr 
        
        # Get the holydays of this year in datetime.date format
        self.holydays = holyday.determine_holydays(self.year)

    def schedule_volunteers(self):
        """schedule_volunteers() is the main method 
        which calls all methods to make a plan for a year quarter. 
        Fill each item in the agenda with the names of two volunteers, 
        one for service 'caretaker' (= 'verzorger') 
        and one for service 'generic' (= 'algemeen').
        """
        # Directive: do not make 'agenda_item' a property of the class, 
        # because from the paramater it is now clear 
        # that the private functions operate on the agenda_item.
        for agenda_item in self.agenda.items:
            # Reset the availability of all persons at the start of each week
            
            # Is the scheduler starting a new week?
            if agenda_item.weeknr != self.currentweek:
                self.currentweek = agenda_item.weeknr
                self._reset_avlblty_counter(self.currentweek)
                self._update_weekend_counter()

            group_not_available = (
                self._determine_group_not_available(agenda_item))
            self._schedule_2_persons(agenda_item, group_not_available)
            self._update_avlblty_counter(agenda_item)
            self._update_persons_not_avlbl(agenda_item)

    def _determine_group_not_available(self, agenda_item):
        """Exclude the persons that are marked as not available for this shift
        from the planning capacity."""
        group_not_available = set( tuple(agenda_item.persons_not_avlbl) )

        # Also not available are the persons with avlblty_counter = 0
        # EXCEPT in the weekends. 
        # Each volunteer must take 1 weekendshift per 4 weeks.
        # If weekend_counter is not exactly 4, 
        # then the person is not available.
        if agenda_item.date.isoweekday() in (6,7):
            dynamic_not_available = set(tuple([ p.name 
                for p in self.all_persons 
                if p.weekend_counter != 4 ]))
        else:
            dynamic_not_available = set(tuple([ p.name 
                for p in self.all_persons 
                if p.avlblty_counter == 0 ]))

        group_not_available.update(dynamic_not_available)
        
        # Also not available are persons with a preference, 
        #       if it is NOT a preference for the current shift.
        # Otherwise the person would be scheduled too early in a week,
        #       and cannot be scheduled any more on the preferred moment.
        # BUT a person with schedule 2 times in 1 week 
        #       is also made not available
        #       after being scheduled once in a week. Which is wrong.
        # This is too complicated. So we leave it to coincidence
        #       that a person with preferences is schedules too soon in a week
        
        return group_not_available
            
    def _schedule_2_persons(self, agenda_item, group_not_available):
        """Update agenda_item.persons with 2 person names.
        One of type caretaker and one of type generalist.
        """
        def helper_pref_person(service, diff_group):
            """If a person has a preference for a weekday-and-shift,
            that person is here chosen before others.
            """
            candidates = []
            persons = [ p for p in self.all_persons 
                        if p.preferred_shifts 
                        and p.service == service ]
            for person in persons:
                if person.name in diff_group:
                    for pref_weekday, pref_shifts\
                            in person.preferred_shifts.items():
                        
                        # It is possible that more than 1 volunteer
                        # has a preference for the same day and shift.
                        # Make a list, and randomly choose one name at return.
                        # And if a person has more than 1 shift preference
                        # on the day, then randomly select 1 shift.
                        # Otherwise the scheduler would always pick
                        # the first day.
                        if (agenda_item.weekday == pref_weekday
                                and agenda_item.shift 
                                in random.sample(pref_shifts,1)): 
                            candidates.append(person.name)
            if candidates:
                [ selected ] = random.sample(candidates, 1)
                return selected
            else:
                return None

        # Do not schedule on a holyday
        if agenda_item.date in self.holydays:
            person_generic = "" 
            person_caretaker = "" 
        else:
            # The two volunteers for this shift 
            # are selected from two different pools
            diff_group_generic = tuple(
                self.generalist_names - group_not_available)
            diff_group_caretaker = tuple(
                self.caretaker_names - group_not_available)
                
            # Select a random sample of 1 person 
            # as a list of 1 item from both sets.
            # Note: function 'random' doesn't operate on a set,
            # so we convert it to a tuple.
            # Note: random.sample() returns a list. 
            # We need the first and only item [0]

            # Choose generalist
            if diff_group_generic:
                pref_person =  helper_pref_person(
                    'algemeen', diff_group_generic)
                if pref_person:
                    person_generic = pref_person
                else:
                    [person_generic] = random.sample(
                        diff_group_generic, 1)
            else:
                person_generic = "" # nobody is available
                
            # Choose caretaker
            if diff_group_caretaker:
                pref_person =  helper_pref_person(
                    'verzorger', diff_group_caretaker)
                if pref_person:
                    person_caretaker = pref_person
                else:
                    [person_caretaker] = random.sample(
                        diff_group_caretaker, 1)
            else:
                person_caretaker = "" # nobody is available
        
        agenda_item.persons.append(person_caretaker)
        agenda_item.persons.append(person_generic)
        
        # The volunteer is scheduled in a weekend.
        # Reset the weekend counter.
        if agenda_item.date.isoweekday() in (6,7):
            persons = self.Volunteers.find([person_caretaker, person_generic])
            for p in persons:
                p.weekend_counter = 0

    def _update_persons_not_avlbl(self, current_agenda_item):
        """Add persons to "persons_not_avlbl" of the
        CURRENT and NEXT day, so that no person is scheduled 
        for two days in a row or for more than one shift on one day.
        Note: This person is also registered in the CURRENT agenda shift
        in 'not_available', but that is no longer of interest
        because the shift is already sheduled."""

        def all_week_not_available(shifts_per_weeks_argument):
            """HELPER function for _update_persons_not_avlbl().
            If a person works e.g. 3 times per *2* weeks
            then the 3 times must be distributed over 2 weeks.
            To prevent that a person gets a 3rd shift in 1 week,
            make the volunteer unavailable for (the rest of) the week.
            The same goes for 2 times in 3 weeks 
            and for 1 shift in two weeks.
            Applicable only in certain shifts_per_weeks combinations:
            (3,2) (2,3) (1,2), so more than 1 week."""

            # Get the instances of class Person for the 2 volunteers 
            # in this shift only if the conditions (see the code) are met.
            # Note: the availability counter must be exactly 1, 
            #   because only then already 2 shifts has been planned, 
            #   of the three available shifts
            #   or 1 shift has been planned of the available 2 shifts.
            for shiftcount, per_weeks in shifts_per_weeks_argument: 
                person_selection= [ 
                        p for p in self.all_persons 
                        if p.name in current_agenda_item.persons 
                        and (p.shifts_per_weeks.shifts == shiftcount
                            and p.shifts_per_weeks.per_weeks == per_weeks
                            and p.avlblty_counter == 1)
                    ]
                if person_selection:
                    # select all agenda items for this week
                    ag_items = [ i for i in self.agenda.items
                                if i.weeknr == current_agenda_item.weeknr ]
                    # make the volunteers unavailable for this week
                    for item in ag_items:
                        for p in person_selection:
                                item.persons_not_avlbl.add(p.name)

                    # If 2 times per 3 weeks, then 
                    # make the next week also unavailable.
                    # Same for 1 time in 2 weeks.
                    if ( (shiftcount == 2 and per_weeks == 3)
                            or (shiftcount == 1 and per_weeks ==2) ):
                        # select all agenda items for the next  week
                        ag_items = [ i for i in self.agenda.items
                                    if i.weeknr == 
                                    current_agenda_item.weeknr + 1 ]
                        # make the agenda items unavailable for this week
                        for item in ag_items:
                            for p in person_selection:
                                    item.persons_not_avlbl.add(p.name)

        current_day = current_agenda_item.date
        next_day = current_day + timedelta(days=1)
        agenda_items = [ i for i in self.agenda.items
                     if (i.date == current_day or i.date == next_day) ]
        for item in agenda_items:
            for person_name in current_agenda_item.persons:
                # '.persons' is: [personname generic, personname caretaker]
                item.persons_not_avlbl.add(person_name)

        # Make the person unavailable for the rest of the week,
        # because the capacity must be distributed
        # over more than one week.
        all_week_not_available( [(3,2),(2,3),(1,2)] )
        
        #TODO it is possible that a person has a shift 
        #   on the last day of the quarter.
        #   The scheduler of the next quarter has no knowledge 
        #   of te former planning.
        #   And thus a person can be scheduled 
        #   on the first day of the new quarter: two days in a row.
        #   Solution: register the date for the persons 
        #   in "nietInPeriode" in the csv source file.

    def _update_avlblty_counter(self, agenda_item):
        """Decrease avlblty_counter for the current week."""
        
        #We need the objects here, not just te names.
        persons = [ p for p in self.all_persons 
                    if p.name in agenda_item.persons ]
        # persons = 
        #   [instance of a person_generic, instance of a person_caretaker]
        for p in persons:
            # Prevent counting below zero. 
            # Use max() which return the maximum value of two.
            p.avlblty_counter = max(0, p.avlblty_counter-1)

    def _update_weekend_counter(self):
        """Every 4 weeks a volunteer must participate in a pool for 
        weekend scheduling. When a person has been scheduled,
        the weekend_counter is set to 0. At the start of a new 
        week the scheduler increments the weekend_counter."""
        
        for person in self.all_persons:
            # Prevent counting above 4.
            person.weekend_counter = min(4, person.weekend_counter + 1)

    def _reset_avlblty_counter(self, currentweek):
        """A volunteer must not be in more shifts 
        than is indicated in his/her shifts_per_weeks preference.
        At the start of each week, reset the avlblty_counter 
        with the number of shifts that the person 
        is willing to work in a week."""

        for person in self.all_persons:
            if person.avlblty_counter == 0:
                # EXCEPT when a person's preference is 1x per 2 weeks.
                # Then the reset is done every ODD week. 
                if not ( person.shifts_per_weeks.shifts == 1 
                        and person.shifts_per_weeks.per_weeks == 2
                        and currentweek % 2 ):
                    person.avlblty_counter = (
                        person.shifts_per_weeks.shifts)

    def _apply_static_rules(self):
        """Initialise the agenda data 'persons not_available' 
        with the preferences of each volunteer i.e.
        persons who don't want to be in a certain shift,
        or who don't want to work on a certain day of the week,
        or who don't want to work on specific dates."""

        for person in self.all_persons:
            # person is not working on a specific day of week
            # on a specific shift
            for item in person.not_on_shifts_per_weekday.items():
                weekday, shifts = item
                for shift in shifts:
                    #TODO HIER BEGRIJP IK NIETS VAN
                    #found_items = self.agenda.finditem(
                    #    weekday = weekday, shift = shift)
                    found_items = []
                    for ag_item in self.agenda.items:
                        if ((ag_item.shift == shift) 
                                and (ag_item.weekday == weekday)):
                            found_items.append(ag_item)
                    for i in found_items:
                        i.persons_not_avlbl.add(person.name)
                        #print(i)

            # person is not working between dates 
            # person.not_in_timespan: 
            #   e.g. [ '22-4-2023, 29-3-2023, 2-1-2023>3-1-2023' ]
            for timespan in person.not_in_timespan:
                found_items = self.agenda.finditem(timespan=timespan)
                for item in found_items:
                    item.persons_not_avlbl.add(person.name)

    def write_agenda_to_csv_file(self, filename):
        """Write the agenda to the csv file <filename>."""
        
        dateformat = "%-d %b" # day - short monthname
        
        with open(filename, 'w') as f:
            writer = csv.writer(f, delimiter=const.CSV_DELIMITER, 
                quotechar='"', quoting=csv.QUOTE_ALL)
            row = (f"Hospice planning {str(self.quarter)}e kwartaal "
                   f'{str(self.year)}, versie {str(self.version)}')
            writer.writerow([row])
            #writer.writerow(["Productiedatum", datetime.now()])
            writer.writerow([])
            
            weekscount = 13 # number of weeks in a quarter
            # from the first day of a quarter to the last + 1
            weekrange = range( 
                (self.quarter -1) * weekscount +1, 
                (self.quarter * weekscount) + 1 )

            for pagebreak_indicator, week in enumerate(weekrange):
                # Pagebreak after every two weeks
                if pagebreak_indicator > 1 and not (pagebreak_indicator % 2):
                    writer.writerow(["pagebreak"])

                #for i in range(1,): writer.writerow([])
                writer.writerow(["","","","", "WEEK " + str(week)])
                writer.writerow([])
                writer.writerow(["", "maandag", "dinsdag", "woensdag", 
                    "donderdag", "vrijdag", "zaterdag", "zondag"])
                
                # get the agenda items for this week
                ag_items = [i for i in self.agenda.items 
                            if i.weeknr == week ]

                # row with dates, below 'week' indication
                dates = OrderedSet(tuple(
                    datetime.strftime(i.date, dateformat) 
                    for i in ag_items))
                row = ["dienst"]
                row.extend(list(dates))
                writer.writerow(row) 
                
                # if a shift has no volunteer, 
                #   fill the cell with 'not available'
                no_volunteer_in_shift = (
                    lambda person: '#N/A' if person == "" else person)

                # A row for each shift, with the names of 
                # 7 caretakers and 7 general service persons
                for shift in range(1,5):
                    caretakers = [ i.persons[0] 
                        for i in ag_items if i.shift == shift ]
                    row = [const.SHIFTNUMBER_LABEL_LOOKUP[shift]]
                    row.extend(list(map(no_volunteer_in_shift, caretakers)))
                    writer.writerow(row) 
                    generalists = [ i.persons[1] 
                        for i in ag_items if i.shift == shift ]
                    row = [""]
                    row.extend(list(map(no_volunteer_in_shift, generalists)))
                    writer.writerow(row) 
                    writer.writerow([])
            print(f'Bestand opgeslagen: {filename}')

    def write_agenda_to_txt_file(self, filename):
        """Write the agenda to the txt file <filename>"""

        with open(filename, 'w') as f:
            weekday_nr = 0
            date = ''
            for i in self.agenda.items:
                if i.weekday == 1 and weekday_nr == 7: 
                    f.write('-'*80 + '\n') # Draw a line at a new week
                weekday_nr = i.weekday
                weekday = const.WEEKDAY_NAME_LOOKUP[weekday_nr]
                if i.date != date:
                    f.write('\n')
                date = i.date
                f.write(f'{i.date} wn:{i.weeknr:>2} {weekday} '
                        f'sh:{i.shift} {i.persons}\n')
            print(f'Bestand opgeslagen: {filename}')

    def prettyprint(self):
        format = \
            '{i.date} ' +\
            'wn:{i.weeknr:>2} ' +\
            'wd:{i.weekday} ' +\
            'sh:{i.shift} ' +\
            '{i.persons}'
        for i in self.agenda.items:
            print(f'{i.date} '
                    f'wn:{i.weeknr:>2} '
                    f'wd:{i.weekday} '
                    f'sh:{i.shift} {i.persons}\n')

    def persons_not_scheduled_in_weekend(self):
        """After de schedule is finished, determine which persons
        are not scheduled in the weekend."""

        scheduled_volunteers = set()
        for ag_item in self.agenda.items:
            if ag_item.weekday in (6,7):
                scheduled_volunteers.update(ag_item.persons)

        all_volunteers = set(tuple([ p.name
            for p in self.all_persons ]))

        unscheduled = all_volunteers - scheduled_volunteers
        if unscheduled:
            unscheduled = list(unscheduled)
            print('\nDe volgende vrijwilligers zijn niet ' + 
                'ingepland in een weekend:')
            for person_name in unscheduled:
                print(person_name)
         
    def persons_not_scheduled(self):
        """After de schedule is finished, determine if the capacity
        of the full group of volunteers has been used."""

        scheduled_volunteers = set()
        for ag_item in self.agenda.items:
            for person_name in ag_item.persons:
                scheduled_volunteers.add(person_name)
        
        all_volunteers = set(tuple([ p.name
            for p in self.all_persons ]))

        unscheduled = all_volunteers - scheduled_volunteers
        if unscheduled:
            print('De volgende vrijwilligers komen niet voor ' + 
                'in de agenda van dit kwartaal:')
            for person_name in unscheduled:
                print(person_name)


def file_exists(filename, extension):
    # Windows: %USERPROFILE%\Downloads
    path = Path(filename + extension)
    if path.is_file():
        print('Proces ONDERBROKEN.'
              + f' Het bestand "{path.name}" bestaat al.'
              + ' Verwijder het of geef het een andere naam.')
        return True
    else:
        return False


def main(year, quarter, version, input_filename):
    agenda = init_agenda.Agenda(year=year, quarter=quarter)
    volunteers = init_volunteers.Volunteers(input_filename)
    scheduler = Scheduler(year, quarter, version, agenda, volunteers) 
    
    # Start scheduling!
    scheduler.schedule_volunteers()
    
    volunteers.show_count()
    
    outfilename = ('./hospice ' 
                   + str(quarter) + 'e kwartaal ' 
                   + str(year) 
                   + ' v. ' + str(version))
    #if file_exists(outfilename, '.csv'):
    #    exit()
    scheduler.write_agenda_to_txt_file(outfilename + '.txt')
    scheduler.write_agenda_to_csv_file(outfilename + '.csv')
    
    scheduler.persons_not_scheduled()
    scheduler.persons_not_scheduled_in_weekend()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Agenda planner voor hospice, Rijssen',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent(
            '''Voorbeeld:
                python hospiceplanner.py 2023 4 1 vrijwilligers-2023-kw1.csv
            ''')
        )
    parser.add_argument('year', 
        help='voor wel jaar de planning gemaakt moet worden', type=int)
    parser.add_argument('quarter', 
        help='voor welk kwartaal', type=int)
    parser.add_argument('version', 
        help='welke versie', type=int)
    parser.add_argument("filename", 
        help='csv bestand met vrijwillergersgegevens')
    args = parser.parse_args()
    print("\nApplication arguments are: ", args)
    main(args.year, args.quarter, args.version, args.filename)
    