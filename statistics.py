import init_volunteers

def count_per_shifts_per_weeks(all_persons):
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
    print(f'gewicht verzorgers: {caretaker_counts}, \ngewicht algemenen: {generalist_counts}')

def days_and_shifts_count(all_persons):
    """Sum the count_of_shifts for each person"""

    count = {}
    services = ('verzorger', 'algemeen')
    for service in services:
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
        pass
    return count['verzorger'], count['algemeen']    


if __name__ == '__main__':
    input_filename = "vrijwilligers-2023-kw2.csv"
    volunteers = init_volunteers.Volunteers(input_filename)
    print()
    count_per_shifts_per_weeks(volunteers.persons)
    print()
    verzorgers_dasc, algemenen_dasc = days_and_shifts_count(volunteers.persons)
    print(f'Aantal shifts niet van verzorgers: {verzorgers_dasc}')
    print(f'Aantal shifts niet van algemenen: {algemenen_dasc}')
