import init_volunteers

def count_shifts_per_weeks(all_persons):
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
    return caretaker_counts, generalist_counts

def show_days_and_shifts_count(all_persons):
    """Sum the count_of_shifts for each person"""

    count = {}
    innercount = {}
    for service in ('verzorger', 'algemeen'):
        for id, prs in enumerate(prs for prs in all_persons
                              if prs.service == service):
            length = 0
            for shifts in prs.not_on_shifts_per_weekday.values():
                length += len(shifts)
            # 7 x 4 = 28 shifts in a week.
            # Do for each person 28 -/- count of shifts
            # so we can have like 20/28 as an indication
            # of the persons capacity for the planning.
            innercount[id + 1] = 28 - length
        count[service] = innercount
        print(f'{service}: {count[service]}')
    # Now get avarage, median and modus.
    
    #indication = [ round(val/28, 2) for val in count_caretaker[service].values() ]
    #print(indication)    


if __name__ == '__main__':
    input_filename = "vrijwilligers-2023-kw2.csv"
    volunteers = init_volunteers.Volunteer(input_filename)
    cc, gc = count_shifts_per_weeks(volunteers.persons)
    show_days_and_shifts_count(volunteers.persons)