#!/usr/bin/env python3
import os
import re
import json
import urllib.parse
import urllib.request
import datetime
import argparse

# Command-line options
arg_parser = argparse.ArgumentParser(description="Forwards notifications from relevant logfiles")
arg_parser.add_argument("logdir", help="Directory containing all log files")
arg_parser.add_argument("--slack", help="A Slack webhook if notifications should be forwarded", type=str)
arg_parser.add_argument("--retention", help="Time, in days, to retain log files", default=2, type=int)
args = arg_parser.parse_args()

# Get the last time this script was run
with open("lastrun.log", "r") as f:
    lastrun = f.read()
    if lastrun != "":
        lastrun = datetime.datetime.fromisoformat(lastrun)
    else:
        lastrun = datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc) # The beginning of time ;)

# Write the current time early to prevent a race condition whereby logs are missed if they arrive during this script's execution
with open("lastrun.log", "w") as f:
    currentrun = datetime.datetime.now(datetime.timezone.utc)
    f.write(currentrun.isoformat())

# List all files in the directory
logfiles = [f for f in os.listdir(args.logdir) if os.path.isfile(os.path.join(args.logdir, f))]

# Finds any logs created after the last scan (we can safely assume the client is reporting in UTC as it was designed to do so)
# However, a clock desync could result in missed logs
for f in logfiles:
    m = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}\:\d{2}\:\d{2}(?:\.\d{6})[+-]\d{2}:\d{2})", f) # Extract the time from the filename
    
    if m is not None:
        logtime = datetime.datetime.fromisoformat(m.group(1)).replace(tzinfo=datetime.timezone.utc)

        # If the log has not been processed in a previous run
        if logtime > lastrun:
            if args.slack is not None:
                # Sends a webhook notification to Slack
                with open(os.path.join(args.logdir, f)) as logfile:
                    logdata = json.load(logfile)

                    # POST body for incoming webhook
                    notification_message = {
                        "attachments": [
                            {
                                "fallback": f"{logdata['MachineName']}: {logdata['Message']}",
                                "color": "#D27CD8",
                                "title": logdata["MachineName"],
                                "text": logdata["Message"],
                                "footer": "Default Notification Service",
                                "ts": logdata["TimeGenerated"]
                            }
                        ]
                    }
                    webhook_data = json.dumps(notification_message).encode("utf-8")

                    # The webhook URL is the only dynamic part of the script
                    request = urllib.request.Request(args.slack, webhook_data)
                    request.add_header("Content-Type", "application/json")
                    response = urllib.request.urlopen(request)

        # Throw away old logfiles (>2 days)
        if logtime < currentrun - datetime.timedelta(days=args.retention):
            os.remove(os.path.join(args.logdir, f))
