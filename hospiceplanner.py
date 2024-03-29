"""Hospiceplanner is a scheduler for a very specific case. 
In The Netherlands, Rijssen there is an organisation who 
looks after dying people to make their last days or weeks
as comfortable as possible.

The organisation has about 50 volunteers who need to be 
scheduled in 4 shifts (of 4 hours) each day, starting at 7 PM.
Each shift is scheduled for two volunteers: one caretaker
(a specialist) and one generalist. There are two groups
of volunteers. 
At night there are no volunteers but only professionals.
A schedule is made per a quarter of a year,
so for 13 weeks in advance.

There are many constraints:
- the number of shifts per weeks (like 1,1 or 2,1 or 3,2 etc.)
- the shifts on which the volunteer is not willing to work,
    for example not on saterday shift 1,2,3,4 and not on 
    sunday shift 1
- the shifts that have a preference, for example preferred
    shifts on tuesday shift 1, and thursday shift 1
- the days off in the quarter
- volunteers must not be scheduled two days in a row
- volunteers must not be scheduled more than once a day
- volunteers are requiered to work in one weekend per 
    two weeks, but no more than twice a week

The personal preferences are available in a sourcefile
(spreadsheet) which is updated quarterly. The sourcefile
is read in init_volunteers.py.
"""
__author__ = "Bob Ambrosius"
__version__ = "1.0"

import argparse
from collections import Counter
import csv
from datetime import datetime
from datetime import timedelta
import locale
from pathlib import Path
import random
import textwrap

from ordered_set import OrderedSet

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
    
    Attributes:
        year: (int)
            The year being scheduled.
        quarter: (int)
            The quarter being scheduled.
        version: (int)
            The version of the produced schedule.
        Volunteers: (Volunteers)
            One instance of class Volunteers
        all_persons: (Person)
            tuple of all instances Person
        generalist_names: (set)
            Set of person names who's service is 'algemeen'.
        caretaker_names: (set)
            Set of person names who's service is 'caretaker'.
        currentweek: (int)
            The week that is being scheduled.
        holydays: (tuple)
            Date_objects that are a holyday for hospice. 
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
                self._reset_availability_counter(self.currentweek)
                self._update_weekend_counter()

            group_not_available = (
                self._determine_group_not_available(agenda_item))
            self._schedule_2_persons(agenda_item, group_not_available)
            self._update_availability_counter(agenda_item)
            self._update_persons_not_available(agenda_item)

    def _determine_group_not_available(self, agenda_item):
        """Return the set of persons that are marked as 
        not available for the current shift.
        """
        group_not_available = set(tuple(agenda_item.persons_not_available))

        # Also not available are the persons with availability_counter = 0
        # EXCEPT in the weekends (isoweeknumbers 6,7). 
        # Each volunteer must take 1 weekendshift per WEEKENDCOUNTER weeks.
        # The person is only available for the weekend
        # if the weekendcounter is exactly WEEKENDCOOUNTER.
        
        # BUT persons who have a shifts_per_weeks of (2,1) or (3,2)
        # are sometimes unavailable. Namely only then if 
        # they already are in 2 shifts this week.
        # Without this exception they could be scheduled for more 
        # than 2 times a week, and that is too much.
        # We only have to test if the person is this week in 2 shifts or more.
        if agenda_item.date.isoweekday() in (6, 7):
            # It's a weekend.
            # Search persons with more than 1 shifts so far this week
            # and save them in a list.
            persons_scheduled_this_week = ([
                ag_item.persons 
                for ag_item in self.agenda.items 
                if ag_item.weeknr == agenda_item.weeknr])
            flatlist = [item for sublist in persons_scheduled_this_week 
                        for item in sublist]
            # Get a dict of all scheduled persons 
            # and count-of scheduled this week
            cnt = Counter(flatlist)
            # Extract the persons that are scheduled more than once.
            # They are not available.
            scheduled_2_times = [key for key in cnt.keys() if cnt[key] > 1]

            dynamic_not_available = (set(tuple([
                p.name for p in self.all_persons 
                if p.weekend_counter != const.WEEKENDCOUNTER 
                or p.name in scheduled_2_times])))
        else:
            # Not a weekend day. Normal rules apply.
            # Unavailable if counter == 0.
            dynamic_not_available = set(tuple([
                p.name for p in self.all_persons 
                if p.availability_counter == 0]))

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
            persons = [
                p for p in self.all_persons
                if p.preferred_shifts
                and p.service == service]
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
                        # the first day in the range.
                        if (agenda_item.weekday == pref_weekday
                                and agenda_item.shift 
                                in [random.choice(pref_shifts)]):
                            candidates.append(person.name)
            if candidates:
                return random.choice(candidates)
            else:
                return None

        def remove_persons_with_future_prefs(service, diff_group, agenda_item):
            """Remove from diff_group the persons that have a preference for
            shifts in the future. If we plan them too soon, they are no
            longer available for shifts that have their preference.
            """
            current_weekday = agenda_item.weekday
            current_shift = agenda_item.shift
            
            # Make a list of persons that heve a preferred shift
            tmp_group = [(
                p.name, p.preferred_shifts)
                for p in self.all_persons
                if p.service == service and p.preferred_shifts]
            
            result = []
            for prs, pref in tmp_group:
                # if the current workdsy is in the pref workdays,
                # and the current shift in that wotkday,
                # than do not remove the person from the
                # available persons, because it IS the preferred
                # day and shift matching the current day and shift.
                if not (current_weekday in pref.keys()
                        and current_shift in pref[current_weekday]):
                    for pref_weekday in pref.keys():
                        # If the pref_weekday is in the future,
                        # Add this person. She wil be discarded for
                        # this agenda item.
                        if pref_weekday > current_weekday:
                            result.append(prs)
                            break
                        else:
                            # Else check if there are future shifts
                            # on the current workday.
                            for pref_shift in pref[pref_weekday]:
                                # AND if the pref_shift is later on the day
                                if pref_shift > current_shift:
                                    # Then add the person to the list of
                                    # persons to be discarded 
                                    # for the current shift.
                                    result.append(prs)
                                    break

            for person in result:
                # Do not remove any person if there is only one in diff_group
                # for then we would have no one left for this shift.
                # In that case no preference is honoured.
                if len(diff_group) > 1:
                    diff_group.discard(person)

        # Do not schedule on a holyday
        if agenda_item.date in self.holydays:
            person_generic = "" 
            person_caretaker = "" 
        else:
            # The two volunteers for this shift 
            # are selected from two different pools
            diff_group_generic = self.generalist_names - group_not_available
            diff_group_caretaker = self.caretaker_names - group_not_available
                
            remove_persons_with_future_prefs(
                'algemeen', diff_group_generic, agenda_item)
            remove_persons_with_future_prefs(
                'verzorger', diff_group_caretaker, agenda_item)

            # Select a random person from both sets.
            # Note: function 'random' doesn't operate on a set,
            # so we convert it to a tuple.

            # Choose generalist
            if diff_group_generic:
                diff_group_generic = tuple(diff_group_generic)
                pref_person = helper_pref_person(
                    'algemeen', diff_group_generic)
                if pref_person:
                    person_generic = pref_person
                else:
                    person_generic = self.Volunteers\
                        .get_optimal_person(diff_group_generic)
            else:
                person_generic = ""  # nobody is available
                
            # Choose caretaker
            if diff_group_caretaker:
                diff_group_caretaker = tuple(diff_group_caretaker)
                pref_person = helper_pref_person(
                    'verzorger', diff_group_caretaker)
                if pref_person:
                    person_caretaker = pref_person
                else:
                    person_caretaker = self.Volunteers\
                        .get_optimal_person(diff_group_caretaker)
            else:
                person_caretaker = ""  # nobody is available
        
        agenda_item.persons.append(person_caretaker)
        agenda_item.persons.append(person_generic)
        
        # If the volunteer is scheduled in a weekend,
        # reset the weekend counter So that she will
        # not be scheduled in a weekend for the next
        # three weeks (untill the counter reaches WEEKENDCOUNTER).
        if agenda_item.date.isoweekday() in (6, 7):
            persons = self.Volunteers.search([
                person_caretaker, person_generic])
            for p in persons:
                if p.name not in const.PERSONS_ALWAYS_IN_WEEKEND:
                    p.weekend_counter = 0

    def _update_persons_not_available(self, current_agenda_item):
        """Add persons to "persons_not_available" of the
        CURRENT and NEXT day, so that no person is scheduled 
        for two days in a row or for more than one shift on one day.
        Note: This person is also registered in the CURRENT agenda shift
        in 'not_available', but that is no longer of interest
        because the shift is already sheduled.
        """

        def all_week_not_available(shifts_per_weeks_argument):
            """HELPER function for _update_persons_not_available().
            If a person works e.g. 3 times per *2* weeks
            then the 3 times must be distributed over 2 weeks.
            To prevent that a person gets a 3rd shift in 1 week,
            make the volunteer unavailable for (the rest of) the week.
            The same goes for 2 times in 3 weeks 
            and for 1 shift in two weeks.
            Applicable only in certain shifts_per_weeks combinations:
            (3,2) (2,3) (1,2), so more than 1 week.
            """

            # Get the instances of class Person for the 2 volunteers 
            # in this shift only if the conditions (see the code) are met.
            # Note: the availability counter must be exactly 1, 
            #   because only then already 2 shifts has been planned, 
            #   of the three available shifts
            #   or 1 shift has been planned of the available 2 shifts.
            for shiftcount, per_weeks in shifts_per_weeks_argument:
                person_selection = [p for p in self.all_persons
                        if p.name in current_agenda_item.persons
                        and (p.shifts_per_weeks.shifts == shiftcount
                        and p.shifts_per_weeks.per_weeks == per_weeks
                        and p.availability_counter == 1)]
                if person_selection:
                    # select all agenda items for this week
                    ag_items = [i for i in self.agenda.items
                                if i.weeknr == current_agenda_item.weeknr]
                    # make the volunteers unavailable for this week
                    for item in ag_items:
                        for p in person_selection:
                            item.persons_not_available.add(p.name)

                    # If 2 times per 3 weeks, then 
                    # make the next week also unavailable.
                    # Same for 1 time in 2 weeks.
                    if ((shiftcount == 2 and per_weeks == 3)
                            or (shiftcount == 1 and per_weeks == 2)):
                        # select all agenda items for the next  week
                        ag_items = [i for i in self.agenda.items
                                    if i.weeknr == 
                                    current_agenda_item.weeknr + 1]
                        # make the agenda items unavailable for this week
                        for item in ag_items:
                            for p in person_selection:
                                item.persons_not_available.add(p.name)

        current_day = current_agenda_item.date
        next_day = current_day + timedelta(days=1)
        agenda_items = [i for i in self.agenda.items
                        if (i.date == current_day or i.date == next_day)]
        for item in agenda_items:
            for person_name in current_agenda_item.persons:
                # '.persons' is: [personname generic, personname caretaker]
                item.persons_not_available.add(person_name)

        # Make the person unavailable for the rest of the week,
        # because the capacity must be distributed
        # over more than one week if the person works
        # on 2 or more shifts per week or once in 2 weeks.
        all_week_not_available([(3, 2), (2, 3), (1, 2)])
        
        # TODO it is possible that a person has a shift 
        # on the last day of the quarter.
        # The scheduler of the next quarter has no knowledge 
        # of te former planning.
        # And thus a person can be scheduled 
        # on the first day of the new quarter: two days in a row.
        # Solution: register the date for the persons 
        # in "nietInPeriode" in the csv source file.

    def _update_availability_counter(self, agenda_item):
        """Decrease availability_counter for the 2 persons in the agenda item.
        The persons have 1 less availability for the rest of the week.
        If a person has shift_per_weeks = (1,1) then she is not
        available for the rest of the week.
        """
        # We need the objects here, not just te names.
        persons = [p for p in self.all_persons
                   if p.name in agenda_item.persons]
        # persons = 
        #   [instance of a person_generic, instance of a person_caretaker]
        for p in persons:
            # Prevent counting below zero. 
            # Use max() which return the maximum value of two.
            p.availability_counter = max(0, p.availability_counter - 1)

    def _update_weekend_counter(self):
        """Every WEEKENDCOUNTER weeks a volunteer must participate in a pool
        for weekend scheduling. When a person has been scheduled,
        the weekend_counter is set to 0. At the start of a new 
        week the scheduler increments the weekend_counter.
        """
        for person in self.all_persons:
            # Prevent counting above WEEKENDCOUNTER.
            person.weekend_counter = (
                min(const.WEEKENDCOUNTER, person.weekend_counter + 1))

    def _reset_availability_counter(self, currentweek):
        """A volunteer must not be in more shifts 
        than is indicated in his/her shifts_per_weeks preference.
        At the start of each week, reset the availability_counter 
        with the number of shifts that the person 
        is willing to work in a week.
        """
        for person in self.all_persons:
            if person.availability_counter == 0:
                # EXCEPT when a person's preference is 1x per 2 weeks.
                # Then the reset is done every ODD week. 
                if not (person.shifts_per_weeks.shifts == 1 
                        and person.shifts_per_weeks.per_weeks == 2
                        and currentweek % 2):
                    person.availability_counter = (
                        person.shifts_per_weeks.shifts)

    def _apply_static_rules(self):
        """Initialise tagenda.item.persons not_available 
        with the preferences of each volunteer i.e.
        persons who don't want to be in a certain shift,
        or who don't want to work on a certain day of the week,
        or who don't want to work on specific dates.
        """
        for person in self.all_persons:
            # person is not working on a specific day of week
            # on a specific shift
            for weekday, shifts in person.not_on_shifts_per_weekday.items():
                for shift in shifts:
                    for ag_item in self.agenda.searchitems(weekday, shift):
                        ag_item.persons_not_available.add(person.name)

            # person is not working between dates 
            # person.not_in_timespan: 
            #   e.g. [ '22-4-2023, 29-3-2023, 2-1-2023>3-1-2023' ]
            for timespan in person.not_in_timespan:
                for ag_item in self.agenda.searchitems(timespan=timespan):
                    ag_item.persons_not_available.add(person.name)

    def write_agenda_to_csv_file(self, filename):
        """Write the agenda to the csv file <filename>.
        """
        # TODO write to .xlsx file 
        dateformat = "%-d %b"  # day - short monthname
        
        with open(filename, mode='w', encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=const.CSV_DELIMITER, 
                quotechar='"', quoting=csv.QUOTE_ALL)
            row = (f"Hospice planning {str(self.quarter)}e kwartaal "
                   f'{str(self.year)}, versie {str(self.version)}')
            writer.writerow([row])
            writer.writerow([])
            
            weekscount = 13  # number of weeks in a quarter
            # from the first day of a quarter to the last + 1
            weekrange = range( 
                (self.quarter - 1) * weekscount + 1,
                (self.quarter * weekscount) + 1)

            for pagebreak_indicator, week in enumerate(weekrange):
                # Pagebreak after every two weeks
                if pagebreak_indicator > 1 and not (pagebreak_indicator % 2):
                    writer.writerow(["pagebreak"])

                writer.writerow(["", "", "", "", "WEEK " + str(week)])
                writer.writerow([])
                writer.writerow(["", "maandag", "dinsdag", "woensdag",
                                 "donderdag", "vrijdag", "zaterdag", "zondag"])
                
                # get the agenda items for this week
                ag_items = [i for i in self.agenda.items 
                            if i.weeknr == week]

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
                for shift in range(1, 5):
                    caretakers = [i.persons[0]
                                  for i in ag_items if i.shift == shift]
                    row = [const.SHIFTNUMBER_LABEL_LOOKUP[shift]]
                    row.extend(list(map(no_volunteer_in_shift, caretakers)))
                    writer.writerow(row) 
                    generalists = [i.persons[1] 
                        for i in ag_items if i.shift == shift]
                    row = [""]
                    row.extend(list(map(no_volunteer_in_shift, generalists)))
                    writer.writerow(row) 
                    writer.writerow([])
            print(f'Bestand opgeslagen: {filename}')

    def write_agenda_to_txt_file(self, filename):
        """Write the agenda to the txt file <filename>
        """
        with open(filename, 'w') as f:
            weekday_nr = 0
            date = ''
            for item in self.agenda.items:
                if item.weekday == 1 and weekday_nr == 7: 
                    f.write('-' * 80 + '\n')  # Draw a line at a new week
                weekday_nr = item.weekday
                weekdayname = const.WEEKDAY_NAME_LOOKUP[weekday_nr]
                if item.date != date:
                    f.write('\n')
                date = item.date
                f.write(f'{item.date} wn:{item.weeknr:>2} {weekdayname} '
                        f'sh:{item.shift} {item.persons}\n')
            print(f'Bestand opgeslagen: {filename}')

    def not_scheduled_shifts(self):
        """Report the number shifts that could not be scheduled,
        Seperate for caretakers and generalists, and total.
        """
        caretakers = [ag_item for ag_item in self.agenda.items
                      if not ag_item.persons[0]
                      and ag_item.date not in self.holydays]
        generalists = [ag_item for ag_item in self.agenda.items
                       if not ag_item.persons[1]
                       and ag_item.date not in self.holydays]
        cc = len(caretakers)
        gc = len(generalists)
        print(f'Aantal ongepland diensten, verzorgers: {cc}, '
              f'algemenen: {gc}. Totaal: {cc + gc}') 

    def persons_not_scheduled_in_weekend(self):
        """Report which persons are not scheduled in the weekend.
        """
        scheduled_volunteers = set()
        for ag_item in self.agenda.items:
            if ag_item.weekday in (6, 7):
                scheduled_volunteers.update(ag_item.persons)

        all_volunteers = set(tuple([
            p.name for p in self.all_persons]))

        unscheduled = all_volunteers - scheduled_volunteers
        if unscheduled:
            unscheduled = list(unscheduled)
            print('\nDe volgende vrijwilligers zijn niet ' + 
                'ingepland in het weekend:')
            for person in self.Volunteers.search(unscheduled):
                print(f'{person.name:20} {person.service:10} '
                      f'({person.shifts_per_weeks.shifts},'
                      f'{person.shifts_per_weeks.per_weeks}) ' 
                      f'{person.not_on_shifts_per_weekday}'
                      )
         
    def persons_not_scheduled(self):
        """Report if the capacity of the full group of volunteers
        has been used.
        """
        scheduled_volunteers = set()
        for ag_item in self.agenda.items:
            for person_name in ag_item.persons:
                scheduled_volunteers.add(person_name)
        
        all_volunteers = set(tuple([
            p.name for p in self.all_persons]))

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


def main(args):
    year = args.year
    quarter = args.quarter
    version = args.version
    input_filename = args.filename
    agenda = init_agenda.Agenda(year=year, quarter=quarter)
    volunteers = init_volunteers.Volunteers(input_filename)
    scheduler = Scheduler(year, quarter, version, agenda, volunteers) 
    
    # Start scheduling!
    scheduler.schedule_volunteers()
    if args.verbose:
        volunteers.show_count()
    
    outfilename = ('./hospice ' 
                   + str(quarter) + 'e kwartaal ' 
                   + str(year) 
                   + ' v. ' + str(version))
    # if file_exists(outfilename, '.csv'):
    #    exit()
    scheduler.write_agenda_to_txt_file(outfilename + '.txt')
    scheduler.write_agenda_to_csv_file(outfilename + '.csv')
    
    scheduler.not_scheduled_shifts()
    
    if args.verbose:
        scheduler.persons_not_scheduled()
        scheduler.persons_not_scheduled_in_weekend()
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Agenda planner voor hospice, Rijssen',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """Voorbeeld:
                python hospiceplanner.py 2023 4 1 vrijwilligers-2023-kw1.csv
            """))
    parser.add_argument('year',  
        help='voor wel jaar de planning gemaakt moet worden', type=int)
    parser.add_argument('quarter', 
        help='voor welk kwartaal', type=int)
    parser.add_argument('version', 
        help='welke versie', type=int)
    parser.add_argument("filename", 
        help='csv bestand met vrijwillergersgegevens')
    parser.add_argument('-v', '--verbose', 
        help='More information about results of scheduling',
        action='store_true')
    args = parser.parse_args()
    
    if args.verbose:
        print("\nApplication arguments: ", args)

    main(args)
