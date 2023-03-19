from datetime import date
from datetime import timedelta
from dateutil.easter import easter


def determine_holydays(year):
    """Calculate the days of <year>.
    Returns a tuple of datetime.date instances.
    """
    days = []
    easter_date = easter(year)
    yearstr = str(year)
    days.append(date.fromisoformat(yearstr + '-01-01'))  # nieuwjaarsdag
    days.append(easter_date)  # 1e paasdag
    days.append(easter_date + timedelta(days=1))  # 2e paasdag
    days.append(easter_date + timedelta(days=40 - 1))  # hemelvaart
    days.append(easter_date + timedelta(days=50 - 1))  # 1e pinksterdag
    days.append(easter_date + timedelta(days=51 - 1))  # 2e pinksterdag
    days.append(date.fromisoformat(yearstr + '-04-27'))  # koningsdag
    days.append(date.fromisoformat(yearstr + '-12-25'))  # 1e kerstdag
    days.append(date.fromisoformat(yearstr + '-12-26'))  # 2e kerstdag
    days.append(date.fromisoformat(yearstr + '-12-31'))  # oudjaarsdag
    days.append(date.fromisoformat((str(year + 1)) + '-01-01'))  # niewjaarsdag

    # return a tuple
    return tuple(days)
