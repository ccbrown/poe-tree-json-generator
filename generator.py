#!/usr/bin/env python

import codecs, csv, json, shlex, struct, subprocess, sys

json_data = {
	'groups': {},
	'root': { 'g': 0, 'o': 0, 'oidx': 0, 'sa': 0, 'da': 0, 'ia': 0, 'out': []},
	'nodes': [],
}

stats = dict()

with open('./Stats.csv', 'r') as f:
	data = csv.DictReader(f)
	for row in data:
		stats[int(row['Rows'])] = row

stat_descriptions = dict()

with codecs.open('./stat_descriptions.txt', encoding='utf-16') as f:
	stat_description_lines = f.readlines()

with codecs.open('./passive_skill_stat_descriptions.txt', encoding='utf-16') as f:
	stat_description_lines += f.readlines()

for i in range(len(stat_description_lines)):
	if stat_description_lines[i].encode('utf-8').strip() == 'description':
		i += 1
		parameters = stat_description_lines[i].encode('utf-8').split()[1:]
		i += 1
		variants = []
		variant_count = int(stat_description_lines[i].encode('utf-8').split()[0])
		for j in range(variant_count):
			i += 1
			variants.append(shlex.split(stat_description_lines[i].encode('utf-8')))

		stat_descriptions[tuple(parameters)] = {
			'parameters': parameters,
			'variants': variants,
		}

def parameter_match(range, n):
	split = range.split('|')

	if len(split) == 1:
		return split[0] == '#' or int(split[0]) == int(n)

	return (split[0] == '#' or int(split[0]) <= int(n)) and (split[1] == '#' or int(split[1]) >= int(n))

def stat_text(stat_values):
	ret = []
	
	for description in stat_descriptions.itervalues():
		parameter_values = []
		should_add_description = False

		for parameter in description['parameters']:
			if parameter in stat_values:
				parameter_values.append(stat_values[parameter])
				should_add_description = True
			else:
				parameter_values.append('0')

		if should_add_description:
			for variant in description['variants']:
				should_use = False
				for i in range(len(parameter_values)):
					if parameter_match(variant[i], parameter_values[i]):
						should_use = True
						break
				
				if should_use:
					ret.append(subprocess.check_output(['./boost-formatter', variant[len(parameter_values)]] + parameter_values))
					break

	return ret

passive_skills = dict()

with open('./PassiveSkills.csv', 'r') as f:
	data = csv.DictReader(f)
	for row in data:
		passive_skills[int(row['Unknown8'])] = row

		stat_ids = json.loads(row['Data0'])
		stat_values = dict()
		for i in range(len(stat_ids)):
			stat = stats[stat_ids[i]]
			stat_values[stat['Id']] = row['Stat%d' % (i + 1)]

		node_json_data = {
			'id': int(row['Unknown8']),
			'icon': row['Icon'].replace('.dds', '.png'),
			'ks': row['IsKeystone'] == 'True',
			'not': row['IsNotable'] == 'True',
			'dn': row['Name'],
			'm': row['IsJustIcon'] == 'True',
			's': row['IsSocket'] == 'True',
			'spc': [], # TODO: what is this?
			'sd': stat_text(stat_values),
			'sa': stat_values['base_strength'] if 'base_strength' in stat_values else 0,
			'da': stat_values['base_dexterity'] if 'base_dexterity' in stat_values else 0,
			'ia': stat_values['base_intelligence'] if 'base_intelligence' in stat_values else 0,
			'out': []
		}

		json_data['nodes'].append(node_json_data)

with open('./PassiveSkillGraph.psg', 'rb') as f:
	graph_data = f.read()

graph_position = 0

def read_graph_byte():
	global graph_data, graph_position
	ret = struct.unpack('<B', graph_data[graph_position])[0]
	graph_position += 1
	return ret

def read_graph_word():
	global graph_data, graph_position
	ret = struct.unpack('<I', graph_data[graph_position:graph_position+4])[0]
	graph_position += 4
	return ret

def read_graph_float():
	global graph_data, graph_position
	ret = struct.unpack('f', graph_data[graph_position:graph_position+4])[0]
	graph_position += 4
	return ret

if read_graph_byte() != 2:
	print 'invalid graph version'
	sys.exit(1)

unknown_count = read_graph_byte()

for i in range(unknown_count):
	unknown = read_graph_byte()

root_count = read_graph_word()

for i in range(root_count):
	root_id = read_graph_word()
	json_data['root']['out'].append(root_id)

group_count = read_graph_word()

for i in range(group_count):
	x = read_graph_float()
	y = read_graph_float()
	
	group_json_data = {
		'x': x, 'y': y,
		'oo': {}, # TODO: what is this?
		'n': [],
	}

	passive_count = read_graph_word()

	for j in range(passive_count):
		skill_id = read_graph_word()
		skill = passive_skills[skill_id]
		orbit_radius = read_graph_word()
		orbit_position = read_graph_word()

		connections = read_graph_word()

		node_json_data = json_data['nodes'][int(skill['Rows'])]

		for k in range(connections):
			node_json_data['out'].append(read_graph_word())
		
		node_json_data['g'] = i + 1
		node_json_data['o'] = orbit_radius
		node_json_data['oidx'] = orbit_position

		group_json_data['n'].append(skill_id)

	json_data['groups'][i + 1] = group_json_data


with open('./merge.json', 'r') as f:
    json_data.update(json.loads(f.read()))

def texture_available(texture):
	global json_data

	for image in json_data['skillSprites']['normalActive']:
		if texture in image['coords']:
			return True

	for image in json_data['skillSprites']['notableActive']:
		if texture in image['coords']:
			return True


	return False

# replace images we don't have with a placeholder
for node in json_data['nodes']:
	has_texture = False

	if node['ks']:
		for image in json_data['skillSprites']['keystoneActive']:
			if node['icon'] in image['coords']:
				has_texture = True
				break

		if not has_texture:
			node['icon'] = 'Art/2DArt/SkillIcons/passives/KeystonePainAttunement.png'
	elif node['not']:
		for image in json_data['skillSprites']['notableActive']:
			if node['icon'] in image['coords']:
				has_texture = True
				break

		if not has_texture:
			node['icon'] = 'Art/2DArt/SkillIcons/passives/savant.png'
	elif node['m']:
		for image in json_data['skillSprites']['mastery']:
			if node['icon'] in image['coords']:
				has_texture = True
				break

		if not has_texture:
			node['icon'] = 'Art/2DArt/SkillIcons/passives/MasteryGroupMace.png'
	elif node['s']:
		node['icon'] = 'Art/2DArt/SkillIcons/passives/chargeint.png'
	else:
		for image in json_data['skillSprites']['normalActive']:
			if node['icon'] in image['coords']:
				has_texture = True
				break

		if not has_texture:
			node['icon'] = 'Art/2DArt/SkillIcons/passives/chargestr.png'

print json.dumps(json_data)
