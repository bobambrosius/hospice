def count_shifts_per_weeks(all_persons):
    caretakers = [ p for p in all_persons if p.service == 'verzorger']
    generalist = [ p for p in all_persons if p.service == 'algemeen']
    caretaker_counts = {}
    generalist_counts = {}
    spw_variants = ((1,1),(2,1),(1,2),(3,2),(2,3))
    for shifts, weeks in spw_variants:
        caretaker_counts['count_'+str(shifts)+'_'+str(weeks)] = len(
            [p for p in caretakers 
             if p.shifts_per_weeks['shiftcount'] == shifts
             and p.shifts_per_weeks['per_weeks'] == weeks
            ])
        generalist_counts['count_'+str(shifts)+'_'+str(weeks)] = len(
            [p for p in generalist 
             if p.shifts_per_weeks['shiftcount'] == shifts
             and p.shifts_per_weeks['per_weeks'] == weeks
            ])
    return caretaker_counts, generalist_counts

