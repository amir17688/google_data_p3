class UnexpectedReuqestDataException(Exception):
    def __str__(self):
        return '''unexpect request data

Usage:

python sqlmap.py -u "http://%s/sqlmap?url=[target]&data=[sqli]"
python sqlmap.py -u "http://%s/sqlmap?url=[target]&is_params=1" --data="id=[sqli]&name=aa"'''


class InvalidWebSocketURLException(Exception):
    def __str__(self):
        return 'Invalid WebSocket Url, example: ws://127.0.0.1/'


class TimeoutWithoutResponseException(Exception):
    def __str__(self):
        return 'Time exceeded without any response'
