from collections import Counter
import const
import init_volunteers

SERVICES = ('algemeen', 'verzorger')


def invert_not_on_shifts_per_weekday(all_persons):
    """Get the inverse, so on_shifts_per_weekday
    """
    prs_on_shift_per_weekday_per_service = {}
    weekdaysrange = (1,2,3,4,5,6,7)
    #weekdaysrange = (6,7)
    shiftrange = (1,2,3,4)
    for service in SERVICES:
        persons = [ prs for prs in all_persons if prs.service == service ]
        prs_on_shift_per_weekday = {}
        for person in persons:
            if person.name == 'Inge Beltman':
                a = person.not_on_shifts_per_weekday
                pass
            inverse = {}
            # For convenient reading set shifts_per_weeks on key: day 0
            inverse[0] = tuple(person.shifts_per_weeks)
            weekday_and_shifts = {}
            for weekday, shifts in person.not_on_shifts_per_weekday.items():
                weekday_and_shifts[weekday] = shifts
            for d in weekdaysrange:
                if d not in weekday_and_shifts.keys():
                    inverse[d] = (1,2,3,4)
                else:
                    prs_shifts = []
                    for s in shiftrange:
                        if not s in weekday_and_shifts[d]:
                            prs_shifts.append(s)
                    if prs_shifts:
                        inverse[d] = tuple(prs_shifts)
                prs_on_shift_per_weekday[person.name] = inverse
        prs_on_shift_per_weekday_per_service[service] = prs_on_shift_per_weekday 
    return prs_on_shift_per_weekday_per_service


def verzorgers_in_weekend(all_persons):
    verzorgers = []
    for prs in all_persons:
        if prs.service == 'verzorger':
            a = prs.not_on_shifts_per_weekday.items()
            for weekday, shifts in prs.not_on_shifts_per_weekday.items():
                if weekday not in (6,7):
                    verzorgers.append(prs)
    return verzorgers
    

def whoswho(all_persons):
    """Wich id belongs to wich name?
    """
    id_name_per_service = {}
    for service in SERVICES:
        id_name = {}
        for id, prs in enumerate(prs for prs in all_persons
                              if prs.service == service):
            id_name[id+1] = prs.name
        id_name_per_service[service] = id_name
    return id_name_per_service

def count_collisions(not_on_spwd_pp_per_service):
    """For each service, for each person, 
    register the day_and_shift collision.
    A day and shift is e.g. ('do', 2).
    If a person doesn't work on the shift
    AND there are others also for the same shift, 
    the number of collisions is calculated.
    """
    # Make a list of all items 'not_in_spw_pp'.
    # Example [ ('ma',1), ('ma',2), ('ma',1) ...]
    list_ = []
    for service in SERVICES:
        for id in not_on_spwd_pp_per_service[service]:
            list_.extend(not_on_spwd_pp_per_service[service][id])
    # Make a dict with key=(day,shift) and value= count of the day_and_shift
    count_of_day_and_shift = Counter(list_)
        
    # For each person, register the collision count for each day_and_shift
    # of that person.
    collisions_per_service = {}
    for service in SERVICES:
        collisions = {}
        for id in not_on_spwd_pp_per_service[service]:
            collisions[id] = 0 # initialise the counter
            for day_and_shift in not_on_spwd_pp_per_service[service][id]:
                count = count_of_day_and_shift[day_and_shift]
                collisions[id] += count
        collisions_per_service[service] = collisions
    return collisions_per_service


def shifts_per_weeks_per_person(all_persons):
    """Report per shift per pserson the type of shifts_per_weeks. """
    
    shifts_per_weeks_per_service = {}
    for service in SERVICES:
        shifts_per_weeks = {}
        for id, prs in enumerate(prs for prs in all_persons
                              if prs.service == service):
            # Make a tuple for each person
            shifts_per_weeks[id+1] = (prs.shifts_per_weeks.shifts, prs.shifts_per_weeks.per_weeks)
        # Add the dict to the 'service' key
        shifts_per_weeks_per_service[service] = shifts_per_weeks
    return shifts_per_weeks_per_service 


def count_per_shifts_per_weeks(all_persons):
    """Report how many persons of each service type 
    have a shifts_per_weeks variant. """

    caretakers = [ p for p in all_persons if p.service == 'verzorger']
    generalist = [ p for p in all_persons if p.service == 'algemeen']
    caretaker_counts = {}
    generalist_counts = {}
    spw_variants = ((1,1),(2,1),(1,2),(3,2),(2,3))
    for shifts, weeks in spw_variants:
        caretaker_counts['('+str(shifts)+','+str(weeks)+')'] = len(
            [p for p in caretakers 
             if p.shifts_per_weeks.shifts == shifts
             and p.shifts_per_weeks.per_weeks == weeks
            ])
        generalist_counts['('+str(shifts)+','+str(weeks)+')'] = len(
            [p for p in generalist 
             if p.shifts_per_weeks.shifts == shifts
             and p.shifts_per_weeks.per_weeks == weeks
            ])
    weight = {}
    weight['verzorger'] = caretaker_counts
    weight['algemeen'] = generalist_counts
    return weight


def not_on_shifts_per_weekday_pp(all_persons):
    """Get data not_in_shifts_per_weekday for each person.
    Result: dict of prs-id, tuple with tuples vor each weekday, shift.
    Example: verzorger: { 1: (('ma',1), ('ma',2)), 2: (('ma',1), ('vr',4)) }"""
    
    not_in_spwd_pp_per_service = {}
    for service in SERVICES:
        not_in_spw_pp = {}
        for id, prs in enumerate(prs for prs in all_persons
                              if prs.service == service):
            list_ = []
            for weekday, shifts in prs.not_on_shifts_per_weekday.items():
                for shift in shifts:
                    list_.append((const.WEEKDAY_NAME_LOOKUP[weekday], shift))
            not_in_spw_pp[id+1] = tuple(list_)
        not_in_spwd_pp_per_service[service] = not_in_spw_pp
    return not_in_spwd_pp_per_service


def not_in_shifts_count_per_person(all_persons):
    """Sum the count_of_not_in_shifts for each person"""
    
    count = {}
    for service in SERVICES:
        innercount = {}
        for id, prs in enumerate(prs for prs in all_persons
                              if prs.service == service):
            length = 0
            for shifts in prs.not_on_shifts_per_weekday.values():
                length += len(shifts)
            # 7 x 4 = 28 shifts in a week.
            # Do for each person 28 -/- count of shifts
            # so we can have like 20/28 as an indication
            # of the persons capacity for the planning.
            innercount[id + 1] = length
            
            """innercount now has 's' of the numerator of the first term
            in the formula: ((28-s)/28) * (1/28) * weight.
            Explanation:
            1/28 is the planningcapacity that a person has 
            if she is available the whole week.
            The weight indicates shifts_per_weeks.
            If a person does not work on 7 shifts per week, then the
            planningcapacity = (28-7)/28 = 21/28 = 3/4 of 1/28 * weight.
            If a person does not work on 0 shifts per week, then the
            planningcapacity = (28-0)/28 = 28/28 = 1 of 1/28 * weight.
            """
        count[service] = innercount
    return count


def capacity_with_shifts(not_in_shift_pp, shifts_per_weeks_per_service_per_person):
    capacity_pp_per_service = {}
    for service in SERVICES:
        capaciteit_totaal = 0
        for (k1, v1), (k2, v2) in zip(not_in_shift_pp[service].items(), 
                                      shifts_per_weeks_per_service_per_person[service].items()):
            #print(k1, '->', v1)
            #print(k2, '->', v2)
            capaciteit_pp = ((28 - v1) / 28) * (1/28) * (v2[0] / v2[1])
            capaciteit_totaal += capaciteit_pp
        capacity_pp_per_service[service] = capaciteit_totaal
    return capacity_pp_per_service


if __name__ == '__main__':
    input_filename = "vrijwilligers-2023-kw2.csv"
    volunteers = init_volunteers.Volunteers(input_filename)
    print()
    
    #weight = count_per_shifts_per_weeks(volunteers.persons)
    #print(f'gewicht: aantal verzorgers: {weight["verzorger"]}')
    #print(f'gewicht: aantal algemenen: {weight["algemeen"]}')
    #print()
    #
    #not_in_shift_pp = not_in_shifts_count_per_person(volunteers.persons)
    #print(f'persoon: aantal NIET in shifts, verzorgers: {not_in_shift_pp["verzorger"]}')
    #print(f'persoon: aantal NIET in shifts, algemenen: {not_in_shift_pp["algemeen"]}')
    #print()
    #
    #shifts_per_weeks_per_service_per_person  = shifts_per_weeks_per_person(volunteers.persons)
    #print(f'persoon: gewicht, verzorgers: {shifts_per_weeks_per_service_per_person["verzorger"]}')
    #print(f'persoon: gewicht, algemenen: {shifts_per_weeks_per_service_per_person["algemeen"]}')
    #print()

    #cap_with_shifts = capacity_with_shifts(not_in_shift_pp, shifts_per_weeks_per_service_per_person)
    #print(f'capaciteit_totaal verzorgers: {cap_with_shifts["verzorger"]}')
    #print(f'capaciteit_totaal algemenen: {cap_with_shifts["algemeen"]}')
    #
    #not_on_spwd_pp_per_service = not_on_shifts_per_weekday_pp(volunteers.persons)
    #print() 
    #print(f'persoon: spwd, verzorgers: {not_on_spwd_pp_per_service["verzorger"]}')
    #print() 
    #print(f'persoon: spwd, algemenen: {not_on_spwd_pp_per_service["algemeen"]}')
    #
    #collission_count = count_collisions(not_on_spwd_pp_per_service)
    #print() 
    #print(f'persoon: aantal botsingen, verzorgers: {collission_count["verzorger"]}')
    #print() 
    #print(f'persoon: aantal botsingen, algemenen: {collission_count["algemeen"]}')
    #  
    #id_to_name = whoswho(volunteers.persons)
    #print() 
    #print(f'verzorgers: {id_to_name["verzorger"]}')
    #print() 
    #print(f'algemenen: {id_to_name["algemeen"]}')
    #
    #verzorgers = verzorgers_in_weekend(volunteers.persons)
    #print()
    #print(verzorgers)

    inospw = invert_not_on_shifts_per_weekday(volunteers.persons)
    with open('inverse.txt', 'w') as f:
        for service in inospw.keys():
            f.write('\n' + service.upper() + '\n')
            for name in inospw[service]:
                f.write(f'{name:22}: ')
                f.write(f'{inospw[service][name]!r}\n')
    print('Inverse van not_on_shifts_per_weekday geschreven naar inverse.txt')
