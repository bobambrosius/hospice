# delimiter for reading and writing csv files
CSV_DELIMITER = ";"

WEEKDAY_LOOKUP = { 'ma':1, 'di':2, 'wo':3, 'do':4, 'vr':5, 'za':6, 'zo':7 }
WEEKDAY_NAME_LOOKUP = { 1:'ma', 2:'di', 3:'wo', 4:'do', 5:'vr', 6:'za', 7:'zo' }

# A person is scheduled in a weekend every WEEKENDCOUNTER weeks
WEEKENDCOUNTER = 2

PERSONS_ALWAYS_IN_WEEKEND = ('Marijke Tibben', 'Janny Seppenwoolde')

DATEFORMAT = '%d-%m-%Y'

# Needed when reporting shifts
SHIFTNUMBER_LABEL_LOOKUP = {
    1: "7-11 uur",
    2: "11-15 uur",
    3: "15-19 uur",
    4: "19-23 uur" }

DEBUG = True
