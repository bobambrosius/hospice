from datetime import date as date_class
from datetime import timedelta
from datetime import datetime
import const

class Agenda:
    """
    Has items. This is a list of instances of class Planningelement.
    Methods:
        finditem()
    """
    def __init__(self, year, quarter):
        self.year = year
        self.quarter = quarter
        self.items = self._initialize() # planningelementlist
        
    def finditem(self,  shift = None, weekday = None, timespan = None):
        """Find an instance of Planningelement.
        Search forward starting with startindex.
        Return an iterable of all the found planningelements.
        """
        endindex = len(self.items)
        
        if (weekday and shift):
            result = []
            for item in self.items:
               if ((item.shift == shift) and (item.weekday == weekday)):
                   result.append(item)
            return result
            
            #result = [ item 
            #    for item in self.items 
            #    if ((item.shift == shift) and (item.weekday == weekday)) ]
            #for i in result:
            #    yield result
            
            #for item in self.items:
            #   if ((item.shift == shift) and (item.weekday == weekday)):
            #       yield item 

        if shift:
            for i in range(0, endindex):
                if self.items[i].shift == shift:
                    yield self.items[i]
        
        if weekday:
            for i in range(0, endindex):
                if self.items[i].weekday == weekday:
                    yield self.items[i]

        # Return all agenda items that are in a timespan
        # timespan has either two dates or one date
        #TODO Als een tijdspanne twee datums heeft 
        #   dan moet de tweede volgen op de eerste, of hetzelfde zijn.
        if timespan:
            const.DATEFORMAT = '%d-%m-%Y'
            dates = timespan.split('>') 
            if len(dates) >1:
                startdate = datetime.strptime(dates[0], 
                            const.DATEFORMAT).date()
                enddate = datetime.strptime(dates[1], 
                          const.DATEFORMAT).date()
            else:
                enddate = startdate = datetime.strptime(dates[0], 
                                      const.DATEFORMAT).date()
                
            currentdate = startdate
            while currentdate <= enddate:
                for i in range(0, endindex):
                    if self.items[i].date == currentdate:
                        # return all agenda items with this date
                        yield self.items[i] 
                currentdate = currentdate + timedelta(days =1) # Next date

    def _initialize(self):
        """Create a list of instances of class Planningelement 
        for a year quarter.
        There are four shifts for each day, 
        so create four planningelements per day.
        """
        startday, endday = self._get_first_and_last_day_of_quarter(
            self.year, self.quarter) 
        planningelementlist = []
        currentday = startday
        while currentday <= endday:
            for shift in range(1,5): # shift '1' to '4' on each day
                element = Planningelement()
                # instance of date_class e.g. datetime.date(2023, 11, 30)
                element.date = currentday 
                element.shift = shift # {1..4}
                element.weeknr = currentday.isocalendar().week # {1..52}
                element.weekday = currentday.isoweekday() # {1..7}
                
                planningelementlist.append(element)
            currentday = currentday + timedelta(days = 1)
        return planningelementlist

    def _get_first_and_last_day_of_quarter(
            self, year, quarter, method = 'after'):
        """We need whole weeks, starting on a monday (isoweekday 1).
        If the first day of a year quarter is not a monday,
        find the first date that is a monday, going back if method = 'before'
        and going forward if method is 'after'.
        And m.m. for the last day of the quarter.
        """
        quarter_end_date = [(3,31), (6,30), (9,30), (12,31)] 
        quarter_start_date = [(1,1), (4,1), (7,1), (10,1)] 
        quarter -= 1 # index starts on 0
        
        month = quarter_start_date[quarter][0]
        day = quarter_start_date[quarter][1]
        startday = date_class(year, month, day)
        
        month = quarter_end_date[quarter][0]
        day = quarter_end_date[quarter][1]
        endday = date_class(year, month, day)
        
        if method == 'after':
            operator = 1 # Add a day
        else:
            operator = -1 # Subtract a day

        while startday.isoweekday() != 1:
            startday = startday + timedelta(days = operator)
        while endday.isoweekday() != 1:
            endday = endday + timedelta(days = operator)
            
        # The last day of the quarter 
        # is the day before monday, so subtract 1 day.
        return startday, endday - timedelta(days = 1) 

class Planningelement:
    """An instance of class Planningelement 
    holds methods and information for one shift of which there are 4 in a day.
    We cannot use namedtuples here because the contents will be changed later.
    """
    def __init__(self):
        self.date = 'date_object'
        # shift: string. '1' = 7:00-11:00, '2' = 11:00-15:00, 
        #   '3' = 15:00-19:00, '4' = 19:00-23:00
        self.shift = ''             
        self.weeknr = 0             # int. 1-52
        self.weekday = 0            # int. isoweekday: 1 = monday. 
        # persons: list of persons in this shift. Max two volunteers
        self.persons = []           
        # persons_not_available: set of persons not allowed in this shift.
        self.persons_not_available = set()  
        # Why a set? Because several functions add a person 
        #   to the set, and the same person must not be added twice.
        
    def __repr__(self):
        return (
            f"date: {self.date}, "
            f"weeknr: {self.weeknr}, "
            f"weekday: {self.weekday}, "
            f"shift: {self.shift}, "
            f"persons: {self.persons}, "
            f"persons_not_available: {self.persons_not_available}"
        )

if __name__ == '__main__':
    agenda = Agenda(year=2023, quarter=1)
    for element in agenda.items:
        print(element)


