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

    def __init__(self, year, quarter, agenda, volunteers):
        self.year = year
        self.quarter = quarter
        self.agenda = agenda
        self.volunteers = volunteers #TODO Waarom dit attribuut?
        # We use 'all_' in the name, for we have subgroups
        self.all_volunteers = self.volunteers.persons 
        # Prepare the agenda with personal wishes,
        # en register the availability in each agenda item .
        self._apply_static_rules() 

        self.group_generic = self.volunteers.group_generic
        self.group_caretaker = self.volunteers.group_caretaker
        # first weeknr of the year quarter
        self.currentweek = self.agenda.items[0].weeknr 
        
        # convert the holydays
        # for easy comparison with agenda.item.date 
        self.holydays = [ datetime.strptime(holyday, const.DATEFORMAT).date()
                         for holyday in const.HOLYDAYS ]

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
            #TODO in plaats van moeilijk steeds onderzoeken of het 
            #       volgende weeknummer is aangebroken kunnen we 
            #       misschien beter over de 13 weeknummers itereren.

            # Is the scheduler starting a new week?
            if agenda_item.weeknr != self.currentweek:
                self.currentweek = agenda_item.weeknr
                self._reset_availability_counter()

            group_not_available = (
                self._determine_group_not_available(agenda_item))
            self._schedule_2_persons(agenda_item, group_not_available)
            self._update_availability_counter(agenda_item)
            self._update_persons_not_available(agenda_item)

    def _determine_group_not_available(self, agenda_item):
        # Exclude the persons that are marked as not available for this shift
        # from the persons that are avalable for the current shift.
        group_not_available = set( tuple(agenda_item.persons_not_available) )

        # Also not available are the persons with availability_counter = 0
        dynamic_not_available = set(tuple([ p.name 
            for p in self.all_volunteers 
            if p.availability_counter == 0 ]))
        group_not_available.update(dynamic_not_available)

        return group_not_available
            
    def _schedule_2_persons(self, agenda_item, group_not_available):
        # Do not schedule volunteers on a holyday
        if agenda_item.date in self.holydays:
            person_generic = "" 
            person_caretaker = "" 
        else:
            # The two volunteers for this shift 
            # are selected from two different pools
            diff_group_generic = tuple(self.group_generic - group_not_available)
            diff_group_caretaker = tuple(self.group_caretaker - group_not_available)
                
            # Select a random sample of 1 person as a list of 1 item from both sets
            # Note: function 'random' doesn't operate on a set,
            # so we convert it to a tuple.
            # Note: random.sample() returns a list. 
            # We need the first and only item [0]
            if diff_group_generic:
                person_generic = random.sample(diff_group_generic, 1)[0]
            else:
                person_generic = "" # nobody is available
            if diff_group_caretaker:
                person_caretaker = random.sample(diff_group_caretaker, 1)[0]
            else:
                person_caretaker = "" # nobody is available
        
        agenda_item.persons.append(person_caretaker)
        agenda_item.persons.append(person_generic)

    def _update_persons_not_available(self, current_agenda_item):

        #HELPER function:
        def all_week_not_available(shiftcount, per_weeks):
            # Only applicable in certain shifts_per_weeks combinations:
            # (3,2) (2,3) (1,2), so more than 1 week.
            # Explanation:
            # If a person works e.g. 3 times per _2_ weeks
            # then the 3 times must be distributed over 2 weeks.
            # To prevent that a person gets a 3rd shift in 1 week,
            # make the volunteer unavailable for (the rest of) the week.
            # The same goes for 2 times in 3 weeks 
            # and for 1 shift in two weeks.

            # Get the instances of class Person for the 2 volunteers in this shift
            # only if the conditions (see the code) are met.
            # Note: the availability counter must be exactly 1, because only then
            #   already 2 shifts has been planned, of the three available shifts.
            person_selection= [ 
                    p for p in self.all_volunteers 
                    if p.name in current_agenda_item.persons 
                    and (p.shifts_per_weeks['shiftcount'] == shiftcount
                        and p.shifts_per_weeks["per_weeks"] == per_weeks
                        and p.availability_counter == 1)
                ]
            if person_selection:
                # select all agenda items for this week
                ag_items = [ i for i in self.agenda.items
                            if i.weeknr == current_agenda_item.weeknr ]
                # make the volunteers unavailable for this week
                for item in ag_items:
                    for p in person_selection:
                            item.persons_not_available.add(p.name)

                # If 2 times per 3 weeks, then make the next week also unavailable.
                # Same for 1 time in 2 weeks.
                if ( (shiftcount == 2 and per_weeks == 3)
                        or (shiftcount == 1 and per_weeks ==2) ):
                    # select all agenda items for the next  week
                    ag_items = [ i for i in self.agenda.items
                                if i.weeknr == current_agenda_item.weeknr + 1 ]
                    # make the agenda items unavailable for this week
                    for item in ag_items:
                        for p in person_selection:
                                item.persons_not_available.add(p.name)

        # Now we must add persons to the set "persons_not_available" of the
        # current and next day, so that no person is scheduled 
        # for two shifts or days in a row or for two shifts in one day.
        # Note: In the current agenda item this person is also registered 
        #   in 'not_available', but it doesn't matter any more 
        #   for that shift is already sheduled.
        
        #TODO it is possible that a person has a shift on the last day of the quarter.
        #   The scheduler of the next quarter has no knowledge of te former planning.
        #   And thus a person can be scheduled on the first day of the new quarter: two days in a row.
        #   Solution: register the date for the persons in "nietInPeriode" in the csv file.
        current_day = current_agenda_item.date
        next_day = current_day + timedelta(days = 1)
        ag_items = [ i for i in self.agenda.items
                     if (i.date == current_day or i.date == next_day) ]
        for item in ag_items:
            for person_name in current_agenda_item.persons:
                # '.persons' is: [person_generic, person_caretaker]
                item.persons_not_available.add(person_name)

        all_week_not_available(3,2)
        all_week_not_available(2,3)
        all_week_not_available(1,2)

    def _update_availability_counter(self, agenda_item):
        # Decrease availability_counter for the current week.
        # We need the objects heer, not just te names
        persons = [ p for p in self.all_volunteers 
            if p.name in agenda_item.persons ]
        # persons = [instance of a person_generic, instance of a person_caretaker]
        for p in persons:
            # Prevent counting below zero. 
            # Use max() which return the maximum value of two.
            p.availability_counter = max(0, p.availability_counter-1)

    def _reset_availability_counter(self):
        # A volunteer must not be in more shifts 
        #   than is indicated in his/her shifts_per_weeks preference.
        # At the start of each week, reset the availability_counter 
        #   with the number of shifts that the person is willing to work in a week.
        for person in self.all_volunteers:
            do_reset = True
            if person.availability_counter == 0:
                # EXCEPT when a person's preference is 1x per 2 weeks.
                # Then the reset is done every ODD week. 
                if ( person.shifts_per_weeks['shiftcount'] == 1 
                        and person.shifts_per_weeks['per_weeks'] == 2
                        and self.currentweek % 2 ):
                    do_reset = False
                if do_reset:
                    person.availability_counter = (
                        person.shifts_per_weeks["shiftcount"])

    def _apply_static_rules(self):
        """Initialise the agenda data 'persons not_available' 
        with the preferences of each volunteer i.e.
        persons who don't want to be in a certain shift,
        or who don't want to work on a certain day of the week,
        or who don't want to work on specific dates.
        """
        for person in self.all_volunteers:
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
                        if ((ag_item.shift == shift) and (ag_item.weekday == weekday)):
                            found_items.append(ag_item)
                    for i in found_items:
                        i.persons_not_available.add(person.name)
                        #print(i)

            # person is not working between dates 
            # person.not_in_timespan: 
            #   e.g. [ '22-4-2023, 29-3-2023, 2-1-2023>3-1-2023' ]
            for timespan in person.not_in_timespan:
                found_items = self.agenda.finditem(timespan = timespan)
                for item in found_items:
                    item.persons_not_available.add(person.name)

    def save_agenda_as_csv(self, filename):
        """Save the agenda to the csv file named <filename>
        """
        shiftnumber_label_lookup = {
            1: "7-11 uur",
            2: "11-15 uur",
            3: "15-19 uur",
            4: "19-23 uur" }
        dateformat = "%-d %b" # day - short monthname
        
        with open(filename, 'w') as f:
            writer = csv.writer(f, delimiter=const.CSV_DELIMITER, 
                quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(["","","","","", "Jaar: " + str(self.year)])
            writer.writerow(["","","","","", "Kwartaal: " + str(self.quarter)])
            writer.writerow(["","","","","", "versie: " + "1"])
            #writer.writerow(["Productiedatum", datetime.now()])
            writer.writerow([])
            
            weekscount = 13 # number of weeks in a quarter
            # from the first day of a quarter to the last + 1
            weekrange = range( 
                (self.quarter -1) * weekscount +1, 
                (self.quarter * weekscount) + 1 )

            for week in weekrange:
                for i in range(1,5): writer.writerow([])
                writer.writerow(["","","","","", "WEEK " + str(week)])
                writer.writerow([])
                writer.writerow(["", "", "maandag", "dinsdag", "woensdag", 
                    "donderdag", "vrijdag", "zaterdag", "zondag"])
                
                # get the agenda items for this week
                ag_items = [ i for i in self.agenda.items if i.weeknr == week ]

                # row with dates, below 'week' indication
                dates = OrderedSet(tuple(
                    datetime.strftime(i.date, dateformat) 
                    for i in ag_items))
                row = ["", "dienst"]
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
                    row = ["", shiftnumber_label_lookup[shift]]
                    row.extend(list(map(no_volunteer_in_shift, caretakers)))
                    writer.writerow(row) 
                    generalists = [ i.persons[1] 
                        for i in ag_items if i.shift == shift ]
                    row = ["", ""]
                    row.extend(list(map(no_volunteer_in_shift, generalists)))
                    writer.writerow(row) 
                    writer.writerow([])
            print(f'\nBestand opgeslagen: {filename}')

    def save_agenda_as_txt(self, filename):
        with open(filename, 'w') as f:
            weekday = 0
            date = ''
            for i in self.agenda.items:
                if i.weekday == 1 and weekday == 7: 
                    f.write('-'*80 + '\n') # Draw a line at a new week
                weekday = i.weekday
                if i.date != date:
                    f.write('\n')
                date = i.date
                f.write(f'{i.date} wn:{i.weeknr:>2} wd:{i.weekday} sh:{i.shift} {i.persons}\n')
            print(f'\nBestand opgeslagen: {filename}')

    def prettyprint(self):
        format = \
            '{i.date} ' +\
            'wn:{i.weeknr:>2} ' +\
            'wd:{i.weekday} ' +\
            'sh:{i.shift} ' +\
            '{i.persons}'
        for i in self.agenda.items:
            print(f'{i.date} wn:{i.weeknr:>2} wd:{i.weekday} sh:{i.shift} {i.persons}')


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
    #volunteers.show_volunteers_info()
    volunteers.show_volunteerscount()
    scheduler = Scheduler(year, quarter, agenda, volunteers) 
    
    # Start scheduling!
    scheduler.schedule_volunteers() 
    outfilename = ('./hospiceplanning ' + str(quarter) + 'e kwartaal ' + str(year) 
        + ' versie ' + str(version))
    #if file_exists(outfilename, '.csv'):
    #    exit()
    if const.DEBUG:
        scheduler.save_agenda_as_txt(outfilename + '.txt')
    scheduler.save_agenda_as_csv(outfilename + '.csv')


if __name__ == '__main__':
    # Show month names of the agenda.csv file in Dutch:
    locale.setlocale(locale.LC_TIME, "nl_NL.utf8")

    parser = argparse.ArgumentParser(
            description='Agenda planner voor hospice, Rijssen',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent('''Voorbeeld:
            python hospiceplanner.py 2023 4 1 vrijwilligers-2023-kw1.csv
        '''))
    parser.add_argument('year', help='voor wel jaar de planning gemaakt moet worden', type=int)
    parser.add_argument('quarter', help='voor welk kwartaal', type=int)
    parser.add_argument('version', help='welke versie', type=int)
    parser.add_argument("filename", help='csv bestand met vrijwillergersgegevens')
    args = parser.parse_args()
    print("\nApplcation arguments are: ", args)
    main(args.year, args.quarter, args.version, args.filename)
    