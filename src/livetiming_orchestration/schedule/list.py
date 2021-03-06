from livetiming_orchestration.schedule import get_events


def run(service, _):
    events = get_events(service)

    if events:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
    else:
        print("No events scheduled")
