from jinja2 import Template
from csv import DictReader
import yaml
from urllib2 import urlopen, URLError

'''
Import data from CSV and create a dynamic HTML based on some templates
'''



class Loader(object):
	'''
	A YAML config file
	'''
	def __init__(self, stream):
		self.configs = [Configuration(self.create_config(record)) for record in yaml.load_all(stream)]

	def write_documents(self):
		for config in self.configs:
			config.write_document()

	def create_config(self, dct):
		source = dct['source']
		try:
			stream = open(source, 'r')
		except IOError:
			try:
				stream = urlopen(source)
			except URLError:
				raise IOError, 'Neither a file nor a URL'
		database = Database(stream)
		document_template = Template(dct['document'])
		entry_template = Template(dct['entry'])
		output = open(dct['output'], 'w')
		if 'filters' in dct:
			filters = dct['filters']
		else:
			filters = {}

		return dict( 
			database=database, document_template=document_template, 
			entry_template=entry_template, output=output, filters=filters)



class Configuration(object):
	def __init__(self, dct):
		self.database = dct['database']
		self.document_template = dct['document_template']
		self.entry_template = dct['entry_template']
		self.output = dct['output']
		if 'filters' in dct:
			self.filters = dct['filters']
		else:
			self.filters = {}

	def read_entries(self):
		return [Entry(record, self.entry_template, self.filters) for record in self.database.read()]

	def render_document(self):
		return Document(self.read_entries(), self.document_template).render()

	def write_document(self):
		self.output.write(self.render_document())
		self.output.close()

class Database(object):
	'''
	A connection to Google spreadsheet or other web based CSV file.
	'''
	def __init__(self, source):
		self.reader = DictReader(source)

	def read(self):
		return self.reader

class Filter(object):

	def filter_split(self, input):
		return input.split(', ')

	def filter_join(self, input):
		return ', '.join(input)

	def filter_append(self, input, append):
		return input + append

	def filter_substitute(self, input, resolvername):
		resolver = Resolver(open('%s.yaml' % resolvername, 'r'))
		return self._filter_substitute(input, resolver)

	def _filter_substitute(self, input, resolver):
		try:
			value = resolver.resolve(input)
			return value
		except KeyError, TypeError:
			return input

	def apply(self, filter, input):
		# split filter into function and options
		lst = filter.split(':')
		function = lst[0]
		options = lst[1:]
		return getattr(self, 'filter_%s' % function)(input, *options)

	def apply_all(self, filters, input):
		value = input
		for filter in filters:
			if not isinstance(value, list) or (filter=='join'):
				value = self.apply(filter, value)
			else:
				# unless filter is join, apply it on each element
				value = [self.apply(filter, x) for x in value]
		return value


class Entry(object):
	'''
	A dictionary of fields.
	'''
	RESERVED_WORDS = ['__init__', 'render', 'apply_all_filters']

	def __init__(self, fields, template='', filters={}):
		'''
		Load and store template and value
		'''
		for field in fields.keys():
			if field in self.__class__.RESERVED_WORDS:
				raise ValueError, '%s is not a permissible field name.' % field
		self.fields = fields
		self.filters = filters
		# filter has to act on field
		for variable in self.filters.keys():
			if variable not in self.fields:
				raise KeyError, 'Filter can only act on an existing field.'
		# if fields are string, decode them
		for (key, value) in self.fields.items():
			if isinstance(value, str):
				self.fields[key] = value.decode('utf-8')
		if template is None:
			lst = ''
			for key in self.fields.keys():
				lst += '{{ %s }}' % key
			self.template = Template(lst)
		else:
			self.template = template

	def render(self):
		'''
		Render a dictionary of fields using a template.
		'''
		self.apply_all_filters()
		return self.template.render(**self.fields)

	def apply_all_filters(self):
		f = Filter()
		if self.filters:
			for (field, filterlist) in self.filters.items():
				self.fields[field] = f.apply_all(filterlist, self.fields[field])
			self.filters = {}

	def __unicode__(self):
		return self.render()

	def __str__(self):
		return self.__unicode__()

	def __getattr__(self, name):
	    '''
	    If attribute is not found, look among fields.
	    '''
	    return unicode(self.fields[name]) 

class Document(object):
	'''
	A list of entries.
	'''
	
	def __init__(self, entries, template):
		'''
		Load and store template and value
		'''
		self.template = template
		self.entries = entries

	def render(self):
		'''
		Render a list of entries using a template.
		'''
		return self.template.render(entries=self.entries)

	def __unicode__(self):
		return self.render()

	def __str__(self):
		return self.__unicode__()


class Resolver(object):
	'''Using a YAML document, change X to dict[X]'''
	def __init__(self, stream):
		'''
		Taking a YAML stream, create a dictionary and store it
		'''
		document = yaml.load(stream)
		if not isinstance(document, dict):
			raise TypeError, 'Resolver only takes documents containing a dictionary.\n %s' % document
		else:
			self.map = document

	def resolve(self, input):
		return self.map[input]

if __name__=='__main__':
	from sys import stdin
	# get config file
	loader = Loader(stdin)
	loader.write_documents()

