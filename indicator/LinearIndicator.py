import backtrader as bt
import datetime
import time
import math

class LinearIndicator(bt.Indicator):
    '''
    This indicator shall produce a signal when price reaches a calculated trend line.

    The indicator requires two price points and date points to serve as X and Y
    values in calcuating the slope and the future expected price trend

    x1 = Date/Time, String in the following format "YYYY-MM-DD HH:MM:SS" of
    the start of the trend
    y1 = Float, the price (Y value) of the start of the trend.
    x2 = Date/Time, String in the following format "YYYY-MM-DD HH:MM:SS" of
    the end of the trend
    y2 = Float, the price (Y value) of the end of the trend.
    '''

    lines = ('linear',)
    params = (
        ('x1', None),
        ('y1', None),
        ('x2', None),
        ('y2', None),
        ('start_datetime', None),
        ('end_datetime', None)
    )

    def __init__(self):
        if self.p.start_datetime is not None:
            self.p.start_datetime = self.__convert_x_to_datetime(self.p.start_datetime)
        else:
            self.p.start_datetime = datetime.datetime.min
        
        if self.p.end_datetime is not None:
            self.p.end_datetime = self.__convert_x_to_datetime(self.p.end_datetime)
        else:
            self.p.end_datetime = datetime.datetime.max

        self.__define_linear_function()

        self.plotinfo.subplot = False
        self.plotinfo.plotlinelabels = True

    def __convert_x_to_datetime(self, x):
        if isinstance(x, datetime.datetime):
            return x
        if isinstance(x, str):
            try:
                dt = datetime.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                dt = datetime.datetime.strptime(x, '%Y-%m-%d')
            return dt
    def __convert_datetime_to_timestamp(self, dt):
        if dt == datetime.datetime.min:
            return 0.0
        elif dt == datetime.datetime.max:
            return math.inf
        else:
            return time.mktime(dt.timetuple())
    
    def __define_linear_function(self):
        self.p.x1 = self.__convert_x_to_datetime(self.p.x1)
        self.p.x2 = self.__convert_x_to_datetime(self.p.x2)

        x1_timestamp = self.__convert_datetime_to_timestamp(self.p.x1)
        x2_timestamp = self.__convert_datetime_to_timestamp(self.p.x2)

        self.m = self.get_slope(
            x1_timestamp, x2_timestamp, self.p.y1, self.p.y2)
        self.B = self.get_y_intercept(self.m, x1_timestamp, self.p.y1)

    def next(self):
        dt = self.data.datetime.datetime()
        date_timestamp = self.__convert_datetime_to_timestamp(dt)

        if dt >= self.p.start_datetime and dt < self.p.end_datetime:
            self.lines.linear[0] = self.get_y(date_timestamp)
        else:
            self.lines.linear[0] = math.nan

    def get_slope(self, x1, x2, y1, y2):
        if math.isclose(x1, 0.0) and math.isclose(x2, math.inf):
            return 0.0
        m = (y2-y1)/(x2-x1)
        return m

    def get_y_intercept(self, m, x1, y1):
        b = y1-m*x1
        return b

    def get_y(self, ts):
        Y = self.m * ts + self.B
        return Y

class HorizontalLinearIndicator(LinearIndicator):
    params = (('y', None), )
    def __init__(self):
        self.p.x1 = datetime.datetime.min
        self.p.y1 = self.p.y
        self.p.x2 = datetime.datetime.max
        self.p.y2 = self.p.y
        super().__init__()