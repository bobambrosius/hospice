# hospiceplanner
Hospiceplanner is a scheduler for a very specific case. 
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
- the days off in the coming quarter
- volunteers must not be scheduled two days in a row
- volunteers must not be scheduled more than once a day
- volunteers are requiered to work in one weekend per 
    two weeks, but no more than twice a week

The personal preferences are available in a spreadsheet 
which is updated quarterly.
