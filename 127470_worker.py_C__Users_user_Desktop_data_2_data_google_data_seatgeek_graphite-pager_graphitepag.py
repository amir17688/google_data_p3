import datetime
import time

import redis
import requests
import requests.exceptions

from graphitepager.config import get_config
from graphitepager.description import get_description
from graphitepager.description import missing_target_description
from graphitepager.graphite_data_record import GraphiteDataRecord
from graphitepager.graphite_target import get_records
from graphitepager.level import Level
from graphitepager.redis_storage import RedisStorage
from graphitepager.utils import parse_args

from notifiers.notifier_proxy import NotifierProxy
from notifiers.hipchat_notifier import HipChatNotifier
from notifiers.pagerduty_notifier import PagerdutyNotifier
from notifiers.pushbullet_notifier import PushBulletNotifier
from notifiers.slack_notifier import SlackNotifier
from notifiers.stdout_notifier import StdoutNotifier


def update_notifiers(notifier_proxy, alert, record, graphite_url):
    alert_key = '{} {}'.format(alert.get('name'), record.target)

    alert_level, value = alert.check_record(record)

    description = get_description(
        graphite_url,
        alert,
        record,
        alert_level,
        value
    )

    notifier_proxy.notify(
        alert,
        alert_key,
        alert_level,
        description
    )


def update_notifiers_missing(notifier_proxy, alert, config):
    graphite_url = config.get('GRAPHITE_URL')
    description = missing_target_description(
        graphite_url,
        alert,
        alert.get('target'),
        Level.NO_DATA,
        None
    )

    notifier_proxy.notify(
        alert,
        alert.get('target'),
        Level.NO_DATA,
        description
    )


def create_notifier_proxy(config):
    redis_url = config.get('REDISTOGO_URL', config.get('REDIS_URL', None))
    STORAGE = RedisStorage(redis, redis_url)

    klasses = [
        HipChatNotifier,
        PagerdutyNotifier,
        PushBulletNotifier,
        StdoutNotifier,
        SlackNotifier,
    ]

    notifier_proxy = NotifierProxy()
    for klass in klasses:
        notifier = klass(STORAGE, config)
        if notifier.enabled:
            print 'Enabling {0}'.format(notifier._domain)
            notifier_proxy.add_notifier(notifier)

    return notifier_proxy


def verify(args):
    config = get_config(args.config)
    config.alerts()
    print 'Valid configuration, good job!'
    return


def run(args):
    config = get_config(args.config)
    alerts = config.alerts()
    notifier_proxy = create_notifier_proxy(config)
    graphite_url = config.get('GRAPHITE_URL')
    while True:
        start_time = time.time()
        seen_alert_targets = set()
        for alert in alerts:
            target = alert.get('target')
            try:
                records = get_records(
                    graphite_url,
                    requests.get,
                    GraphiteDataRecord,
                    target,
                    from_=alert.get('from'),
                )
            except requests.exceptions.RequestException:
                update_notifiers_missing(notifier_proxy, alert, config)
                records = []

            for record in records:
                name = alert.get('name')
                target = record.target
                if (name, target) not in seen_alert_targets:
                    update_notifiers(
                        notifier_proxy,
                        alert,
                        record,
                        graphite_url
                    )
                    seen_alert_targets.add((name, target))
        time_diff = time.time() - start_time
        sleep_for = 60 - time_diff
        if sleep_for > 0:
            sleep_for = 60 - time_diff
            print 'Sleeping for {0} seconds at {1}'.format(
                sleep_for,
                datetime.datetime.utcnow()
            )
            time.sleep(60 - time_diff)


def main():
    command_map = {
        'verify': verify,
        'run': run,
    }
    args = parse_args()
    return command_map[args.command](args)


if __name__ == '__main__':
    main()
