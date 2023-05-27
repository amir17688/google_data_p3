"""vimfuzzer.py generates a stream of random vim commands
Written by Stefan Parviainen
Placed into the Public Domain where applicable. No rights reserved"""

import sys
import re
import random
import traceback
import argparse
import tempfile
import subprocess
import os
import gzip


NUMERIC_COMMAND_EXPR = re.compile(r'(?:\bN(th)?\b|\bNmove\b)')
CTRL_EXPR = re.compile(r'CTRL-([^ ]+)')

def parse_range(char_range):
	"""Parse regex-style character range"""
	chars = []
	if char_range[-1] == '-': # Last dash does not indicate a range so handle it now
		chars.append('-')
		char_range = char_range[:-1]

	# BUG: Ranges can also include CTRL- characters
	# Now all dashes should really indicate ranges
	i = 0
	while i < len(char_range)-1:
		if i != len(char_range) - 1 and char_range[i+1] == '-': # Start of range
			start = char_range[i]
			end = char_range[i+2]
			chars += [unichr(x) for x in range(ord(start), ord(end)+1)]
			i += 2
		else:
			chars.append(char_range[i])
			i += 1
	return chars

REGISTERS = [''] + ['"' + register for register in parse_range('0-9a-zA-Z:.%#=*+~_/')]

def parse_help(helpfile):
	"""Figure out vim commands from the fixed help file"""

	commands = {}
	for key in ['insert', 'normal', 'visual', 'ex']:
		commands[key] = []

	motions = set([])

	# Split help by section
	sections = re.split(r'[=]{4,}', helpfile.read().expandtabs())[1:] # First part has no commands
	for nsection, section in enumerate(sections):
		section_lines = section.split('\n')
		for i, line in enumerate(section_lines):
			if not (line != '' and line[0] == '|'): # Normal line
				continue

			# Handle commands that span multiple lines
			try:
				if section_lines[i+1][0] == ' ': # Line continuation
					line = line + ' ' + section_lines[i+1]
			except IndexError:
				pass


			# Work around bugs in Vim documentation
			if line.startswith('|[<MiddleMouse> '):
				line = '|[<MiddleMouse>| ' + line[16:]
			if line.startswith('|]<MiddleMouse> '):
				line = '|]<MiddleMouse>| ' + line[16:]

			# Get note and comment
			# This is surprisingly difficult since the help file is not well formatted
			try:
				j = line.index('|', 2)
				tag = line[1:j]
				# Skip some commands, handled explicitly elsewhere
				if tag in ['quote', ':', 'i_CTRL-X', 'count']: 
					continue
				k = line.index(' ', 31)
				command = line[j+1:k].strip()
				if nsection in [1, 4, 5, 6, 7]:
					try:
						note = int(line[k:].split()[0])
					except ValueError:
						note = None
						comment = line[k:]
					comment = line[k:].split()[1]
				else:
					note = None
					comment = line[k:]
			except ValueError:
				print 'Malformed input help file'
				print line
				sys.exit(1)

			command = CTRL_EXPR.sub(lambda m: '<C-%s>'%m.group(1), command) # Change CTRL-x to <C-x>
			command = command.replace(' ', '') # Remove whitespace in commands

			# Check if command is an ex command
			if command[0] == ':':
				command += r'<CR>a' # Ex commands expect a newline at the end
				continue # BUG: Skip ex commands for now

			# BUG: These are not handled correctly so skip them
			if tag in ['c_CTRL-R', 'c_CTRL-R_CTRL-R']:
				continue


			# Check if command takes numeric argument (but it's only told in comment)
			if NUMERIC_COMMAND_EXPR.search(comment) and not r'{count}' in command:
				command = '{count}'+command

			# Check if command is a motion
			if note == 1 or nsection == 2 or command in motions:
				motions.add(command)

			tup = (command, tag)
			# Check which modes commands belong to
			if nsection > 0 and nsection != 7 and nsection != 8:
				commands['normal'].insert(0, tup)
				commands['visual'].insert(0, tup)
				if nsection == 9: # Ex mode commands
					commands['ex'].insert(0, tup)
			elif nsection == 7: # Visual mode command
				# This will add some duplicate commands since some are given as normal mode commands as well
				commands['visual'].insert(0, tup)
			elif nsection == 0: # Insert mode command
				commands['insert'].insert(0, tup)

	return commands, motions
		
def generate_command(command, motions):
	"""Generate a concrete command by replacing placeholders with valid values"""

	command = command.replace('["x]', random.choice(REGISTERS))

	command = re.sub(r'\[(.+?)\]', lambda m:m.group(1)[:random.randint(0, len(m.group(1)))], command) # Remove random part of optional command part

	count = random.randint(-1, 10)
	if count == -1:
		count = ''
	command = command.replace('{count}', str(count))

	command = command.replace('{height}', str(random.randint(1, 100)))

	if '{motion}' in command:
		command = command.replace('{motion}', generate_command(random.choice(list(motions)), motions))

	command = command.replace('{number}', '%03d'%random.randint(0, 255))
	command = re.sub(r'{char\d?}', lambda m: unichr(random.choice(range(0x20, 0x7e) + range(0x100, 0x200))), command)

	command = command.replace('{filter}', 'sort<CR>') # Sort should be a pretty safe choice

	# Anything left in {} indicate character ranges
	command = re.sub('{(.*?)}', lambda m: random.choice(parse_range(m.group(1)) if m.group(1) != 'pattern' else '{pattern}'), command)

	command = command.replace('{pattern}', '.{%d}'%(random.randint(0, 10)))


	return command

def main():
	"""Main entrypoint for program"""
	parser = argparse.ArgumentParser(description='Generate stream of random vim commands')
	parser.add_argument('--count', metavar='N', type=int, dest='count', default=10, help='Number of commands to generate')
	parser.add_argument('--verbose', action='store_true', dest='verbose', default=False, help='Print out additional information')
	parser.add_argument('--helpfile', metavar='PATH', dest='helpfile', default=None, help="Location of Vim's index.txt help file")

	args = parser.parse_args()

	# Create temporary help file
	if args.helpfile == None:
		helpfile = tempfile.mktemp(suffix='.txt')
		subprocess.call(['vim', '-c', ':h index', '-c', ':sav %s'%helpfile, '-c', ':qa'])
	else:
		helpfile = args.helpfile

	if helpfile.endswith('.gz'):
		opener = gzip.open
	else:
		opener = open

	commands, motions = parse_help(opener(helpfile))

	# Remove temporary help file
	if args.helpfile == None:
		os.unlink(helpfile)

	# Commands that change mode.
	mode_change = {}
	mode_change['insert'] = ['a', 'A', 'i', 'I', 'gI', 'gi', 'o', 'O', 'c', 'cc', 'C', 'v_c', 'v_r', 'v_s', ':startinsert', ':append', 's', 'S']
	mode_change['normal'] = ['CTRL-[', 'i_CTRL-[', 'i_CTRL-C', 'i_<Esc>', 'c_CTRL-\_CTRL-N', 'c_CTRL-\_GTRL-G', 'v_CTRL-\_CTRL-N', 'v_CTRL-\_GTRL-G', ':visual', ':view']
	mode_change['visual'] = ['CTRL-V', 'V', 'v', '<RightMouse>', 'v_v', 'v_V', 'v_CTRL-V']
	mode_change['ex'] = ['Q']

	mode_mapping = dict([(tag, mode) for mode in mode_change for tag in mode_change[mode]])

	mode = 'normal'
	for _ in range(args.count):

		try:
			command, tag = random.choice(commands[mode])
			if command == 'Q': # Don't enter ex-mode since it's not working well yet
				continue
			new = generate_command(command, motions)
			mode = mode_mapping.get(tag, mode)
		except Exception:
			traceback.print_exc(file=sys.stderr)
			sys.stderr.write('%s, %s, %s\n'%(new, command, mode))
			sys.exit(1)

		if args.verbose:
			print '%s\t%s\t%s' % (new.encode('utf-8'), command.encode('utf-8'), mode)
		else:
			print new.encode('utf-8')

if __name__ == '__main__':
	main()
