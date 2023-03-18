from datetime import date as Date
from datetime import timedelta
from datetime import datetime

import const


class Planningelement:
    """A Planningelement is a daily shift of four hours of which there are 
    four in a day.
    Note: 
    We cannot use namedtuples here because the contents will be changed later.
    """
    # But perhaps a SimpleNamespace will do!!
    def __init__(self):
        self.date = 'date_object'
        # shift: string. '1' = 7:00-11:00, '2' = 11:00-15:00, 
        #   '3' = 15:00-19:00, '4' = 19:00-23:00
        self.shift = 0              # int {1,4}
        self.weeknr = 0             # int. {1-52}
        self.weekday = 0            # int. isoweekday: 1 = monday. 
        # persons: person names scheduled for this shift. Maximum is 2.
        self.persons = []           
        # persons_not_available:
        # set of person names not available for this shift.
        self.persons_not_available = set()  
        # Why a set? Because several functions add a person 
        # to the set, and the same person must not be 
        # in the set more than once.
        
    def __repr__(self):
        return (
            f"date: {self.date}, "
            f"weeknr: {self.weeknr}, "
            f"weekday: {self.weekday}, "
            f"shift: {self.shift}, "
            f"persons: {self.persons}, "
            f"persons_not_available: {self.persons_not_available}"
        )


class Agenda:
    """Agenda has items. This is a list of instances of class Planningelement.
    Methods:
        searchitems()
    """
    def __init__(self, year, quarter):
        self.year = year
        self.quarter = quarter
        self.items = self._initialize()  # planningelementlist
        
    def searchitems(self, weekday=None, shift=None, timespan=None):
        """Search instances of Planningelement.
        Yield the found planningelements one at a time.
        """
        if weekday and shift:
            for ag_item in self.items:
                if ag_item.shift == shift and ag_item.weekday == weekday:
                    yield ag_item

        if timespan:
            dates = timespan.split('>') 
            if len(dates) > 1:
                startdate = datetime.strptime(dates[0], 
                            const.DATEFORMAT).date()
                enddate = datetime.strptime(dates[1], 
                          const.DATEFORMAT).date()
            else:
                enddate = startdate = datetime.strptime(dates[0], 
                                      const.DATEFORMAT).date()
                
            currentdate = startdate
            while currentdate <= enddate:
                for ag_item in self.items:
                    if ag_item.date == currentdate:
                        yield ag_item
                currentdate = currentdate + timedelta(days=1)  # Next date
        
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
            for shift in range(1, 5):  # shift '1' to '4' on each day
                element = Planningelement()
                # instance of Date e.g. datetime.date(2023, 11, 30)
                element.date = currentday 
                element.shift = shift  # {1..4}
                element.weeknr = currentday.isocalendar().week  # {1..52}
                element.weekday = currentday.isoweekday()  # {1..7}
                
                planningelementlist.append(element)
            currentday = currentday + timedelta(days=1)
        return planningelementlist

    def _get_first_and_last_day_of_quarter(
            self, year, quarter, method='after'):
        """We need whole weeks, starting on a monday (isoweekday 1).
        If the first day of a year quarter is not a monday,
        find the first date that *is* a monday,
        going back if method = 'before'
        and going forward if method is 'after'.
        And m.m. for the last day of the quarter.
        """
        quarter_end_date = [(3, 31), (6, 30), (9, 30), (12, 31)] 
        quarter_start_date = [(1, 1), (4, 1), (7, 1), (10, 1)] 
        quarter -= 1  # index starts on 0
        
        month = quarter_start_date[quarter][0]
        day = quarter_start_date[quarter][1]
        startday = Date(year, month, day)
        
        month = quarter_end_date[quarter][0]
        day = quarter_end_date[quarter][1]
        endday = Date(year, month, day)
        
        if method == 'after':
            operator = 1  # Add a day
        else:
            operator = -1  # Subtract a day

        while startday.isoweekday() != 1:
            startday = startday + timedelta(days=operator)
        while endday.isoweekday() != 1:
            endday = endday + timedelta(days=operator)
            
        # The last day of the quarter 
        # is the day before monday, so subtract 1 day.
        return startday, endday - timedelta(days=1) 


if __name__ == '__main__':
    agenda = Agenda(year=2023, quarter=2)
    for element in agenda.items:
        print(element)
