#!/usr/bin/env python3
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Author: Don Atherton
# Web: https://donatherton.co.uk
# Conkycalendar (c) Don Atherton don@donatherton.co.uk

"""
Usage: queries local ics file and displays today's and tomorrow's events in Conky. Set Conky to update when required.
${execp ~/path/to/conkycalendar.py --file ~/path/to/calendar.ics}
"""
import re
from datetime import datetime, timedelta
import argparse
import dateutil.rrule as rrule

parser = argparse.ArgumentParser()
parser.add_argument('--file', nargs=1, required=True)
try:
	args = parser.parse_args()
	calendar_location = args.file[0]
except:
	print("No file location given")

def unescape(component):
	text = re.sub('^.*?:', '', component[0].strip())
	# NOTE: ORDER MATTERS!
	if isinstance(text, str):
		return text.replace('\\N', '\\n')\
			       .replace('\r\n', '\n')\
			       .replace('\\n', '\n')\
			       .replace('\\,', ',')\
			       .replace('\\;', ';')\
			       .replace('\\\\', '\\')
	elif isinstance(text, bytes):
		return text.replace(b'\\N', b'\\n')\
			       .replace(b'\r\n', b'\n')\
			       .replace(b'\n', b'\n')\
			       .replace(b'\\,', b',')\
			       .replace(b'\\;', b';')\
			       .replace(b'\\\\', b'\\')

def process_events(event):
	if 'SUMMARY' in event:
		summary = re.search('SUMMARY.*:.*\n', event)
		summary = unescape(summary)
	else:
		summary = ''
	if 'LOCATION' in event:
		loc = re.search('LOCATION.*:.*\n', event)
		loc = '\n\t' + unescape(loc)
	else:
		loc = ''
	return summary, loc

try:
	calendar_file = open(calendar_location)
	calendar = calendar_file.read()
	calendar_file.close()
except:
	print("Can't open ical file")
try:
	events = calendar.split('BEGIN:VEVENT')
	today = []
	tomorrow = []

	for event in events:
		allday = False

		eventDateTime = re.search('DTSTART.*:.*\n', event)
		if eventDateTime is None:
			continue

		eventDateTime = re.sub('^.*?:', '', eventDateTime[0]).strip()
		if len(eventDateTime) == 15:
			eventDateTime = datetime.strptime(eventDateTime, '%Y%m%dT%H%M%S')
		elif len(eventDateTime) == 16:
			eventDateTime = datetime.strptime(eventDateTime, '%Y%m%dT%H%M%SZ')
		elif len(eventDateTime) == 8:  # All day event - only date
			eventDateTime = datetime.strptime(eventDateTime, '%Y%m%d')
			allday = True

		# Reccurring events
		if 'RRULE' in event:
			ruletext = re.search('RRULE:.*\n', event)
			ruletext = ruletext[0][6:]
			rule = rrule.rrulestr(ruletext, dtstart=eventDateTime)
			eventDateTime = rule.after(datetime.now() - timedelta(days=1))  # Include today

		if datetime.now().date() == eventDateTime.date():
			summary, loc = process_events(event)
			if allday is False:
				if datetime.now() < eventDateTime + timedelta(hours=1):  # So it stays up for an hour after its time
					today.append(eventDateTime.time().strftime('%H:%M') + ' -- ' + summary + loc)
			else:
				today.append(' ' + summary + loc)
		elif datetime.now().date() + timedelta(days=1) == eventDateTime.date():
			summary, loc = process_events(event)
			if allday is False:
				tomorrow.append(eventDateTime.time().strftime('%H:%M') + ' -- ' + summary + loc)
			else:
				tomorrow.append(' ' + summary + loc)

	if len(today) > 0:
		today.sort()
		print('------ Today ------${voffset 3}')
		for entry in today:
			print(entry, '${voffset 3}')
	if len(tomorrow) > 0:
		tomorrow.sort()
		weekday = (datetime.now().date() + timedelta(days=1)).strftime('%A')
		print('${voffset 3}------', weekday, '------${voffset 3}')
		for entry in tomorrow:
			print(entry, '${voffset 3}')
except Exception as e:
	print("Error:", e)
