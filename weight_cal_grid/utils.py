"""Misc. utility and common functions"""


########################################################################


import datetime
import time


########################################################################


def get_latest_sunday(date):
    """Get latest sunday, starting at given date and going back"""
    for i in range(7):
        delta = datetime.timedelta(days=i)
        i_date = date - delta
        if i_date.weekday() == 6:
            return i_date
    raise InternalLogicError()


def get_earliest_sunday(date):
    """Get earliest sunday, starting at given date and going forwards"""
    for i in range(7):
        delta = datetime.timedelta(days=i)
        i_date = date + delta
        if i_date.weekday() == 6:
            return i_date
    raise InternalLogicError()


########################################################################


def get_latest_first(date):
    """Get latest first of month, starting at date and going back"""
    return datetime.date(year=date.year, month=date.month, day=1)


def get_next_first(date):
    """Get earliest first of month, starting at date and going forwards"""
    y = date.year
    m = date.month + 1
    if m > 12:
        m = 1
        y += 1
    return datetime.date(year=y, month=m, day=1)


########################################################################


class AbstractMethodError(Exception):
    """Abstract method has been called"""
    pass


########################################################################


class InternalLogicError(Exception):
    """The internal program logic turns out to be flawed."""
    pass


########################################################################
