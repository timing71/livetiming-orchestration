import datetime
import os
import re

from livetiming_orchestration.schedule import create_event, get_events, update_event
from livetiming_orchestration.schedule.datetime_z import parse_datetime
from livetiming_orchestration.scheduler import EVT_SERVICE_REGEX

DEFAULT_CALENDAR_URL = os.environ.get(
    'CALENDAR_SOURCE_URL',
    'eecbbdriq2erv62pbk1t7mnvqqcdook2@import.calendar.google.com'
)

TAG_TO_SERVICE_CLASS = {
    '24H Proto Series': '24h_series',
    '24H Series': '24h_series',
    '24H TCES': '24h_series',
    '24H': '24h_series',
    'ALMS': 'aslms',
    'CTSC': 'imsa',
    'European Le Mans': 'elms',
    'ELMS': 'elms',
    'Formula 1': 'f1',
    'F1': 'f1',
    'Formula 2': 'f2',
    'F2': 'f2',
    'Formula E': 'formulae',
    'GT4A': 'tsl',
    'GTWC America': 'tsl',
    'GTWC Europe': 'gtwc',
    'GP3 Series': 'f3',
    'F3': 'f3',
    'IMSA': 'imsa',
    'IndyCar': 'indycar',
    'Michelin Le Mans Cup': 'lemanscup',
    'NASCAR': 'nascar',
    'V8 Supercars': 'v8sc',
    'Supercars': 'v8sc',
    'TCA': 'tsl',
    'VLN': 'vln',
    'W': 'wige',
    'WC': 'tsl',
    'WEC': 'wec'
}

_MAPPED_TAGS = {
    '24H': '24H Series',
    'ALMS': 'Asian Le Mans Series',
    'GT4A': 'GT4 America',
    'GTWC America': 'World Challenge USA',
    'TCA': 'TC America',
    'NASCAR': 'NASCAR Cup',
    'WC': 'World Challenge USA',
    'W': 'W Series'
}

# Default arguments per tag can contain a single wildcard, ?,
# which will be replaced when livetiming-schedule assist is run
# interactively. Services with a wildcard will not be scheduled
# non-interactively.
_DEFAULT_ARGS = {
    'F1': '--hidden',
    'GT4A': '--session ?',
    'GTWC America': '--session ?',
    'GTWC Europe': '--tz ?',
    'Formula E': '--hidden',
    'IMSA': '--hidden',
    'TCA': '--session ?',
    'VLN': '--tz 2',
    'W': '-e 31',
    'WC': '--session ?',
    'WEC': '--hidden --hh live-api.hhtiming.com:24688'
}


def add_parser_args(parser):
    parser.add_argument('--calendar', default=DEFAULT_CALENDAR_URL, help='Google calendar URL to source events from')
    parser.add_argument('--dry-run', action='store_true', help='Don\'t actually create events')
    parser.add_argument('--non-interactive', action='store_true', help='Don\'t prompt for input if it would be required')


def run(service, args):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    then = (datetime.datetime.utcnow() + datetime.timedelta(days=14)).isoformat() + 'Z'
    upcoming = service.events().list(
        calendarId=args.calendar,
        orderBy='startTime',
        timeMin=now,
        timeMax=then,
        singleEvents=True
    ).execute().get('items', [])

    scheduled = list(map(_parse_scheduled_event, get_events(service)))

    def already_scheduled(event):
        for scheduled_event in scheduled:
            if event['id'] == scheduled_event['correlationId']:
                return scheduled_event
            if event['service'] == scheduled_event['service']:
                if event['start'] == scheduled_event['start']:
                    if event['end'] == scheduled_event['end']:
                        return scheduled_event
        return False

    def maybe_update_event(event, scheduled):
        if event['updated'] > scheduled['updated']:
            if not args.dry_run:

                event_body = {
                    'id': scheduled['id'],
                    'start': {
                        'dateTime': event['start'].strftime("%Y-%m-%dT%H:%M:%S%z")
                    },
                    'end': {
                        'dateTime': event['end'].strftime("%Y-%m-%dT%H:%M:%S%z")
                    },
                    'summary': scheduled['originalSummary'],
                    'description': 'Automatically updated by livetiming-schedule assist'
                }

                if scheduled.get('correlationId') is not None:
                    event_body['extendedProperties'] = {
                        'private': {
                            'correlationId': scheduled['correlationId']
                        }
                    }

                update_event(
                    service,
                    event_body
                )
                print('Updated: {}'.format(event['summary']))
            else:
                print('Needs update: {}'.format(event['summary']))
        else:
            print("Already scheduled: {}".format(event['summary']))

    for e in upcoming:
        if 'dateTime' not in e['start']:
            print("Skipping event without session time: {}".format(e['summary']))
        else:
            event = _parse_event(e)

            already_scheduled_event = already_scheduled(event)

            if not event['service']:
                print("Skipping event with no associated service: {}".format(e['summary']))
            elif event['summary'].endswith('Event'):
                print("Skipping event without session time: {}".format(e['summary']))
            elif already_scheduled_event:
                maybe_update_event(event, already_scheduled_event)
            else:
                print("New event: {} ({} - {})".format(event['summary'], event['start'], event['end']))

                try:
                    default_args = _get_default_args(event, args)

                    event_body = {
                        'summary': "{} [{}{}]".format(
                            event['summary'],
                            event['service'],
                            ', {}'.format(default_args) if default_args else ''
                        ),
                        'start': {
                            'dateTime': event['start'].strftime("%Y-%m-%dT%H:%M:%S%z")
                        },
                        'end': {
                            'dateTime': event['end'].strftime("%Y-%m-%dT%H:%M:%S%z")
                        },
                        'description': 'Automatically generated by livetiming-schedule assist',
                        'extendedProperties': {
                            'private': {
                                'correlationId': e['id']
                            }
                        }
                    }
                    if not args.dry_run:
                        create_event(service, event_body)
                except NoArgumentSupplied:
                    print("Cannot create event, required argument was not supplied")


MULTI_SPACE_REGEX = re.compile(r'\s+')


def _parse_event(event):
    summary = event['summary']
    tag = summary[1:summary.index(']')]

    return {
        'summary': MULTI_SPACE_REGEX.sub(' ', "{}: {}".format(_map_tag_to_name(tag), summary[summary.index(']') + 1:])),
        'service': TAG_TO_SERVICE_CLASS.get(tag),
        'start': parse_datetime(event['start']['dateTime']),
        'end': parse_datetime(event['end']['dateTime']),
        'id': event['id'],
        'tag': tag,
        'updated': parse_datetime(event['updated'])
    }


def _parse_scheduled_event(event):
    parsed = EVT_SERVICE_REGEX.match(event.get('summary', ''))

    return {
        'id': event['id'],
        'summary': parsed.group('name'),
        'service': parsed.group('service'),
        'start': parse_datetime(event['start']['dateTime']),
        'end': parse_datetime(event['end']['dateTime']),
        'correlationId': event.get('extendedProperties', {}).get('private', {}).get('correlationId'),
        'updated': parse_datetime(event['updated']),
        'originalSummary': event['summary']
    }


def _map_tag_to_name(tag):
    return _MAPPED_TAGS.get(tag, tag)


class NoArgumentSupplied(Exception):
    pass


_ARG_TEMPLATE_CACHE = {}


def _get_default_args(event, my_args):
    tag = event['tag']
    if tag in _DEFAULT_ARGS:
        default_template = _DEFAULT_ARGS[tag]

        if '?' in default_template:
            if tag in _ARG_TEMPLATE_CACHE:
                prompt = '  > Value required for \'{}\' (Enter for previous value {}): '.format(
                    default_template,
                    _ARG_TEMPLATE_CACHE[tag]
                )
            else:
                prompt = '  > Value required for \'{}\': '.format(default_template)

            if not my_args.non_interactive:
                value = input(prompt) or _ARG_TEMPLATE_CACHE.get(tag)

                if value:
                    _ARG_TEMPLATE_CACHE[tag] = value

                    return default_template.replace('?', value)

            raise NoArgumentSupplied()

        if tag == 'WEC' and 'Qualifying' in event['summary']:
            return "{} --qualifying".format(default_template)

        return default_template
    return ''
