import operator

from graphite_data_record import NoDataError
from level import Level


class Alert(object):

    def __init__(self, alert_data, doc_url=None):
        self.alert_data = dict(alert_data)
        self.alert_data['allow_no_data'] = self.alert_data.get(
            'allow_no_data', False)
        self.alert_data['doc_url'] = self.alert_data.get('doc_url', doc_url)
        self.alert_data['exclude'] = set(self.alert_data.get('exclude', []))
        self.alert_data['from'] = self.alert_data.get('from', '-1min')

        self.comparison_operator = self._determine_comparison_operator(
            self.get('warning'),
            self.get('critical')
        )

    def get(self, key, default=None):
        return self.alert_data.get(key, default)

    def documentation_url(self, target=None):
        doc_url = self.get('doc_url')
        if doc_url is None:
            return None

        template = doc_url + '/' + self.get('name')
        if target is None:
            url = template
        else:
            url = template + '#' + target
        return url

    def _determine_comparison_operator(self, warn_value, crit_value):
        if warn_value > crit_value:
            return operator.le
        elif crit_value > warn_value:
            return operator.ge

    def check_record(self, record):
        if record.target in self.get('exclude'):
            return Level.NOMINAL, 'Excluded'
        try:
            value = record.get_last_value()
        except NoDataError:
            return Level.NO_DATA, 'No data'
        if self.comparison_operator(value, self.get('critical')):
            return Level.CRITICAL, value
        elif self.comparison_operator(value, self.get('warning')):
            return Level.WARNING, value
        return Level.NOMINAL, value

    def value_for_level(self, level):
        if level == Level.CRITICAL:
            return self.get('critical')
        elif level in (Level.WARNING, Level.NOMINAL):
            return self.get('warning')
        else:
            return None
