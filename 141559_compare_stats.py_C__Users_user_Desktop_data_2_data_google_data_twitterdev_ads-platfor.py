#!/usr/bin/env python

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib

import oauth2 as oauth
# import requests
import yaml


DOMAIN = 'https://ads-api.twitter.com'
VERBOSE = 0


def main(options):
    global VERBOSE
    account = options.account_id
    headers = options.headers
    if options.veryverbose is True:
        VERBOSE = 2
    elif options.verbose is True:
        VERBOSE = 1
    start = time.clock()
    user_twurl = twurlauth()

    print("Fetching stats for :account_id %s" % account)
    linesep()

    now = datetime.datetime.utcnow()
    if options.start_time:
        start_time = options.start_time
    else:
        st = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        st = st.replace(minute=0, second=0, microsecond=0)
        start_time = st.isoformat()
    if options.end_time:
        end_time = options.end_time
    else:
        et = datetime.datetime.utcnow()
        et = et.replace(minute=0, second=0, microsecond=0)
        et -= datetime.timedelta(seconds=1)
        end_time = et.isoformat()
    print('Current time:\t%s' % now)
    print('Start time:\t%s' % start_time)
    print('End time:\t%s' % end_time)
    linesep()

    # check that we have access to this :account_id
    resource_path = '/0/accounts/%s' % account
    data = get_data(user_twurl, 'GET', headers, DOMAIN + resource_path)

    if len(data) == 0:
        print('ERROR: Could not locate :account_id %s' % account)
        sys.exit(0)

    total_query_count = 0
    total_request_cost = 0
    total_rate_limited_query_count = 0

    if len(options.campaigns) > 0:
        print("\tfetching stats for %s campaigns" % len(options.campaigns))
        (query_count, cost_total,
         rate_limited_query_count) = gather_stats(user_twurl, headers, account, 'campaigns',
                                                  start_time, end_time, options.campaigns)

        for campaign_id in options.campaigns:
            st = re.sub(r'-\d{4}', '', start_time)
            et = re.sub(r'-\d{4}', '', end_time)
            params = {
                'campaign': int(campaign_id, 36),
                'segment': 'tweets',
                'endString': '{0}.000'.format(et),
                'startString': '{0}.000'.format(st)
            }

            qs = urllib.urlencode(params)
            ui_url = 'https://ads.twitter.com/accounts/%s/campaigns_dashboard?%s' % (account, qs)
            print('UI URL: %s' % ui_url)

        total_query_count += query_count
        total_request_cost += cost_total

    linesep()
    print("Total Stats Queries:\t\t%s" % total_query_count)
    print("Total Stats Request Cost:\t%s" % total_request_cost)
    if VERBOSE > 0:
        print("Avg Cost per Query:\t\t%s" % str(total_request_cost / total_query_count))
    print("Queries Rate Limited:\t\t%s" % total_rate_limited_query_count)
    linesep()

    elapsed = (time.clock() - start)
    print('Time elapsed:\t\t\t%s' % elapsed)


def parse_input():
    p = argparse.ArgumentParser(description='Fetch Twitter Ads Account Stats')

    p.add_argument('-a', '--account', required=True, dest='account_id',
                   help='Ads Account ID')
    p.add_argument('-A', '--header', dest='headers', action='append',
                   help='HTTP headers to include')
    p.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                   help='Verbose outputs cost avgs')
    p.add_argument('-vv', '--very-verbose', dest='veryverbose', action='store_true',
                   help='Very verbose outputs API queries made')
    p.add_argument('--start_time', dest='start_time',
                   help='ISO 8601 timestamp for start time')
    p.add_argument('--end_time', dest='end_time',
                   help='ISO 8601 timestamp for end time')
    p.add_argument('-c', '--campaigns', required=True, nargs='+', dest='campaigns')

    args = p.parse_args()

    return args


def twurlauth():
    with open(os.path.expanduser('~/.twurlrc'), 'r') as f:
        contents = yaml.load(f)
        f.close()

    default_user = contents["configuration"]["default_profile"][0]

    CONSUMER_KEY = contents["configuration"]["default_profile"][1]
    CONSUMER_SECRET = contents["profiles"][default_user][CONSUMER_KEY]["consumer_secret"]
    USER_OAUTH_TOKEN = contents["profiles"][default_user][CONSUMER_KEY]["token"]
    USER_OAUTH_TOKEN_SECRET = contents["profiles"][default_user][CONSUMER_KEY]["secret"]

    return CONSUMER_KEY, CONSUMER_SECRET, USER_OAUTH_TOKEN, USER_OAUTH_TOKEN_SECRET


def request(user_twurl, http_method, headers, url):
    CONSUMER_KEY = user_twurl[0]
    CONSUMER_SECRET = user_twurl[1]
    USER_OAUTH_TOKEN = user_twurl[2]
    USER_OAUTH_TOKEN_SECRET = user_twurl[3]

    consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
    token = oauth.Token(key=USER_OAUTH_TOKEN, secret=USER_OAUTH_TOKEN_SECRET)
    client = oauth.Client(consumer, token)

    header_list = {}
    if headers:
        for i in headers:
            (key, value) = i.split(': ')
            if key and value:
                header_list[key] = value

    response, content = client.request(url, method=http_method, headers=header_list)

    try:
        data = json.loads(content)
    except:
        data = None
    return response, data


def get_data(user_twurl, http_method, headers, url):
    data = []

    res_headers, response = request(user_twurl, http_method, headers, url)

    if res_headers['status'] != '200':
        print('ERROR: query failed, cannot continue: %s' % url)
        print('\tHTTP status code: %s' % res_headers['status'])
        sys.exit(0)

    if response and 'data' in response:
        data += response['data']

    while 'next_cursor' in response and response['next_cursor'] is not None:
        cursor_url = url + '&cursor=%s' % response['next_cursor']
        res_headers, response = request(user_twurl, http_method, headers, cursor_url)

        if response and 'data' in response:
            data += response['data']

    return data


def gather_stats(user_twurl, headers, account_id, entity_type, start_time, end_time,
                 input_entities):

    metrics = [
        'billed_charge_local_micro',
        'promoted_tweet_search_impressions',
        'promoted_tweet_timeline_impressions',
        'promoted_tweet_profile_impressions',
        'promoted_tweet_timeline_url_clicks',
        'promoted_tweet_search_url_clicks',
        'promoted_tweet_profile_url_clicks',
        'mobile_conversion_installs',
        'promoted_tweet_app_install_attempts',
        'promoted_tweet_app_open_attempts'
    ]

    metric_list = ','.join(metrics)

    entities = list(input_entities)
    resource_url = DOMAIN + "/0/stats/accounts/%s/%s" % (account_id, entity_type)
    query_params = '?granularity=HOUR&start_time=%s&end_time=%s' % (start_time, end_time)
    query_params += '&metrics=%s' % metric_list
    query_param_entity_name = re.sub(r's$', '_ids', entity_type)

    query_count = 0
    cost_total = 0
    rate_limited_query_count = 0
    limit_sleep_sec = 0

    while entities:
        if limit_sleep_sec > 0:
            print('\t! sleeping for %s' % limit_sleep_sec)
            time.sleep(limit_sleep_sec)
            limit_sleep_sec = 0

        query_entities = []
        limit = 20
        if len(entities) < limit:
            limit = len(entities)

        for _ in range(limit):
            query_entities.append(entities.pop(0))

        entity_params = '&%s=%s' % (query_param_entity_name, ','.join(query_entities))
        stats_url = resource_url + query_params + entity_params

        res_headers, res_data = request(user_twurl, 'GET', headers, stats_url)

        print(stats_url)
        print_results(res_data)

        if 'x-request-cost' in res_headers:
            cost_total += int(res_headers['x-request-cost'])

            if (('x-cost-rate-limit-remaining' in res_headers and
                    int(res_headers['x-cost-rate-limit-remaining']) == 0) and
                    res_headers['status'] == '429'):
                limit_sleep_sec = int(res_headers['x-cost-rate-limit-reset']) - int(time.time())

        if res_headers['status'] == '200':
            query_count += 1

            if VERBOSE > 1:
                print('VERBOSE:\tStats Query:\t%s' % stats_url)

        elif res_headers['status'] == '429':
            print("RATE LIMITED! adding entities back to queue")
            rate_limited_query_count += 1
            entities.extend(query_entities)
        elif res_headers['status'] == '503':
            print("TIMEOUT!")
            print(stats_url)
            entities.extend(query_entities)
        else:
            print("ERROR %s" % res_headers['status'])
            print(res_headers)
            sys.exit(0)

    if VERBOSE > 0:
        print('VERBOSE:\tAvg cost per query:\t%s' % str(cost_total / query_count))

    return query_count, cost_total, rate_limited_query_count


def print_results(res_data):
    for i in res_data['data']:

        billed_charge_local_micro = total_value(i['billed_charge_local_micro'])

        impressions = total_value(i['promoted_tweet_timeline_impressions'])
        impressions += total_value(i['promoted_tweet_search_impressions'])
        impressions += total_value(i['promoted_tweet_profile_impressions'])

        app_clicks = total_value(i['promoted_tweet_timeline_url_clicks'])
        app_clicks += total_value(i['promoted_tweet_search_url_clicks'])
        app_clicks += total_value(i['promoted_tweet_profile_url_clicks'])
        app_clicks += total_value(i['promoted_tweet_app_install_attempts'])
        app_clicks += total_value(i['promoted_tweet_app_open_attempts'])

        installs = total_value(i['mobile_conversion_installs'])

        print('ID:\t%s' % i['id'])
        print('\tSpend:\t%s' % billed_charge_local_micro)
        print('\tImpressions:\t%s' % impressions)
        print('\tApp Clicks:\t%s' % app_clicks)
        print('\tInstalls:\t%s' % installs)
        print('---')

    return True


def total_value(metric):
    """Given a time series of values, sum the values"""

    total = 0
    for i in metric:
        total += i

    return total


def check(data, start_time, end_time, filter_field=None, filter_data=[]):

    d = []

    if data and len(data) > 0:
        for i in data:
            if 'end_time' in i and i['end_time'] and format_timestamp(i['end_time']) < start_time:
                continue
            elif ('start_time' in i and i['start_time'] and
                  format_timestamp(i['start_time']) > end_time):
                continue
            elif i['deleted'] is True and format_timestamp(i['updated_at']) < start_time:
                continue
            elif i['paused'] is True and format_timestamp(i['updated_at']) < start_time:
                continue
            elif filter_field and i[filter_field] not in filter_data:
                continue
            else:
                d.append(i['id'])

    return d


def format_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


def linesep():
    print('-----------------------------------------------')


if __name__ == '__main__':
    options = parse_input()
    main(options)
