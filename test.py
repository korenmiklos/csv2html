# -*- coding: utf-8 -*-
import csv2html as module
import unittest as ut 

from jinja2 import Template
from csv import DictReader, writer
import yaml
from StringIO import StringIO
from collections import Iterable

class TestDatabase(ut.TestCase):
	def create_test_file(self):
		tmpf = StringIO()
		output = writer(tmpf)
		output.writerow(['A', 'B', 'C'])
		output.writerow([1, 2, 3])
		output.writerow([2, 4, 6])

		tmpf.seek(0)

		return tmpf

	def test_accepts_utf8(self):
		stream = StringIO()
		stream.write(u'szőlőfeldolgozó,üzem\n1,2'.encode('utf-8'))
		stream.seek(0)
		db = module.Database(stream)
		self.assertIsInstance(db, module.Database)

	def test_returns_unicode_keys(self):
		stream = StringIO()
		stream.write(u'szőlőfeldolgozó,üzem\n1,2'.encode('utf-8'))
		stream.seek(0)
		db = module.Database(stream)
		record = list(db.read())[0]
		for key in record.keys():
			self.assertIsInstance(key, unicode)

	def test_returns_unicode_values(self):
		stream = StringIO()
		stream.write(u'A,B\nszőlőfeldolgozó,üzem'.encode('utf-8'))
		stream.seek(0)
		db = module.Database(stream)
		record = list(db.read())[0]
		for value in record.values():
			self.assertIsInstance(value, unicode)

	def test_dictreader_is_returned(self):
		tmpf = self.create_test_file()
		db = module.Database(tmpf)
		self.assertIsInstance(db.read(), DictReader)

	def test_accepts_stream(self):
		tmpf = self.create_test_file()
		db = module.Database(tmpf)
		self.assertIsInstance(db, module.Database)

	def test_reader_preserves_order(self):
		tmpf = self.create_test_file()
		db = list(module.Database(tmpf).read())
		self.failUnless(db[1]['A']>db[0]['A'])

	def test_known_values(self):
		tmpf = self.create_test_file()
		db = list(module.Database(tmpf).read())
		self.assertDictEqual(db[0], dict(A='1', B='2', C='3'))
		self.assertDictEqual(db[1], dict(A='2', B='4', C='6'))

class TestLoader(ut.TestCase):
	def test_loader_returns_list(self):
		stream = StringIO()
		dct = {'source': 'file:///dev/null', 'document': '', 'entry': '', 'output': '/dev/null'}
		yaml.dump(dct, stream)
		stream.seek(0)
		self.assertIsInstance(module.Loader(stream).configs, Iterable)

	def test_loader_returns_configs(self):
		stream = StringIO()
		dct = {'source': 'file:///dev/null', 'document': '', 'entry': '', 'output': '/dev/null'}
		yaml.dump(dct, stream)
		stream.seek(0)
		self.assertIsInstance(module.Loader(stream).configs[0], module.Configuration)

	def test_loader_preserves_order(self):
		pass

	def test_write_documents(self):
		stream = StringIO()	
		output = StringIO()	
		dct1 = {'source': 'file:///dev/null', 'document': 'Document one. ', 'entry': '', 'output': '/dev/null'}
		dct2 = {'source': 'file:///dev/null', 'document': 'Document two.', 'entry': '', 'output': '/dev/null'}
		yaml.dump_all([dct1, dct2], stream)
		stream.seek(0)
		loader = module.Loader(stream)

		loader.write_documents()
		output.seek(0)
		self.assertEqual(output.read(), 'Document one. Document two.')


class TestEntry(ut.TestCase):
	def test_entry_accepts_none(self):
		entry = module.Entry({})

	def test_entry_as_string(self):
		entry = module.Entry({}, Template('Dummy template'))
		self.assertEqual(str(entry), 'Dummy template')

	def test_known_examples(self):
		entry = module.Entry(dict(x=1), Template('Value is {{x}}'))
		self.assertEqual(str(entry), 'Value is 1')

	def test_filter_knownvalues(self):
		entry = module.Entry(dict(a='1, 2, 3', b=4), Template(''), dict(a=['split']))
		entry.apply_all_filters()
		self.assertListEqual(entry.fields['a'], ['1', '2', '3'])

	def test_filter_does_not_change_other_field(self):
		entry = module.Entry(dict(a='1, 2, 3', b=4), Template(''), dict(a=['split']))
		entry.apply_all_filters()
		self.assertEqual(entry.fields['b'], 4)

	def test_filter_has_to_act_on_field(self):
		def callable():
			entry = module.Entry(dict(a=1), Template(''), dict(b=['split']))
		self.assertRaises(KeyError, callable)

	def test_filters_are_optional(self):
		entry = module.Entry(dict(a='1, 2, 3', b=4), Template(''))
		entry.apply_all_filters()
		self.assertEqual(entry.fields['a'], '1, 2, 3')

	def test_filters_applied_before_rendering(self):
		entry = module.Entry(dict(a='123', b=4), Template('{{a}}'), dict(a=['append:4']))
		self.assertEqual(entry.render(), '1234')

	def test_filters_not_applied_twice(self):
		entry = module.Entry(dict(a='123', b=4), Template(''), dict(a=['append:4']))
		entry.apply_all_filters()
		entry.apply_all_filters()
		self.assertEqual(entry.fields['a'], '1234')

	def test_field_can_be_reached_directly(self):
		entry = module.Entry(dict(a='1, 2, 3', b=4), Template(''))
		self.assertEqual(entry.b, '4')

	def test_nonexistent_field_cannot_be_reached(self):
		def callable():
			entry = module.Entry(dict(a='1, 2, 3', b=4), Template(''))
			print entry.c
		self.assertRaises(KeyError, callable)

	def test_field_cannot_be_reserved_word(self):
		def callable():
			entry = module.Entry(dict(a='1, 2, 3', render=4), Template(''))
		self.assertRaises(ValueError, callable)
		def callable():
			entry = module.Entry(dict(a='1, 2, 3', apply_all_filters=4), Template(''))
		self.assertRaises(ValueError, callable)

	def test_unicode_to_unicode(self):
		entry = module.Entry(dict(text=u'szőlőfeldolgozó üzem'), Template('{{text}}'))
		self.assertEqual(entry.render(), u'szőlőfeldolgozó üzem')

class TestDocument(ut.TestCase):
	def test_document_renders_something(self):
		document = module.Document([], Template('Dummy template'))
		self.assertEqual(str(document), 'Dummy template')

	def test_document_renders_unicode(self):
		document = module.Document([], Template(u'szőlőfeldolgozó üzem'))
		self.assertEqual(document.render(), u'szőlőfeldolgozó üzem')

	def test_document_renders_entries(self):
		entry = module.Entry({}, Template('An entry.'))
		document = module.Document([entry]*3, Template('{% for entry in entries %}{{entry}}{% endfor %}'))
		self.assertEqual(str(document), 'An entry.An entry.An entry.')


class TestConfiguration(ut.TestCase):
	def test_configuration_accepts_dictionary(self):
		db = module.Database(StringIO())
		dct = {'database': db, 'document_template': Template(''), 
		'entry_template': Template(''), 'output': StringIO()}
		conf = module.Configuration(dct)
		self.assertIsInstance(conf, module.Configuration)

	def test_document_template_is_compiled(self):
		db = module.Database(StringIO())
		dct = {'database': db, 'document_template': Template(''), 
		'entry_template': Template(''), 'output': StringIO()}
		conf = module.Configuration(dct)
		self.assertIsInstance(conf.document_template, Template)

	def test_entry_template_is_compiled(self):
		db = module.Database(StringIO())
		dct = {'database': db, 'document_template': Template(''), 
		'entry_template': Template(''), 'output': StringIO()}
		conf = module.Configuration(dct)
		self.assertIsInstance(conf.entry_template, Template)

	def test_entry_has_filters(self):
		stream = StringIO()
		stream.write('''A,B,C
			1,2,3
			4,5,6''')
		stream.seek(0)
		db = module.Database(stream)
		dct = {'database': db, 'document_template': Template('A document.'), 
		'entry_template': Template(''), 'output': StringIO(), 
		'filters': {'A': ['split', 'join']}}
		conf = module.Configuration(dct)
		self.assertDictEqual(conf.read_entries()[0].filters, {'A': ['split', 'join']})

	def test_blank_templates_are_fine(self):
		pass

	def test_read_entries(self):
		stream = StringIO()
		stream.write('''A,B,C
			1,2,3
			4,5,6''')
		stream.seek(0)
		db = module.Database(stream)
		dct = {'database': db, 'document_template': Template('A document.'), 
		'entry_template': Template(''), 'output': StringIO()}
		conf = module.Configuration(dct)
		[self.assertIsInstance(entry, module.Entry) for entry in conf.read_entries()]

	def test_render_document(self):
		db = module.Database(StringIO())
		dct = {'database': db, 'document_template': Template('A document.'), 
		'entry_template': Template(''), 'output': StringIO()}
		conf = module.Configuration(dct)
		self.assertEqual(conf.render_document(), 'A document.')

	def test_render_document_can_be_repeated(self):
		db = module.Database(StringIO())
		dct = {'database': db, 'document_template': Template('A document.'), 
		'entry_template': Template(''), 'output': StringIO()}
		conf = module.Configuration(dct)
		conf.render_document()
		self.assertEqual(conf.render_document(), 'A document.')

	def test_write_document(self):
		db = module.Database(StringIO())
		output = StringIO()
		dct = {'database': db, 'document_template': Template('A document.'), 
		'entry_template': Template(''), 'output': output}
		conf = module.Configuration(dct)
		conf.write_document()
		output.seek(0)
		self.assertEqual(output.read(), 'A document.')

	def test_default_encoding_is_utf8(self):
		stream = StringIO()
		stream.write(u'A,B,C'.encode('utf-8'))
		stream.write(u'ő,ú,á'.encode('utf-8'))
		stream.write(u'é,ű,í'.encode('utf-8'))
		stream.seek(0)
		db = module.Database(stream)
		dct = {'database': db, 'document_template': Template('{% for entry in entries %}{{entry}}{% endfor %}'), 
		'entry_template': Template('{{A}}, {{B}}, {{C}}'), 'output': StringIO()}
		conf = module.Configuration(dct)
		document = conf.render_document()
		try:
			document.decode('utf-8')
		except Exception:
			self.fail('Could not decode string as UTF-8.')

	def test_output_rendered_in_utf8(self):
		stream = StringIO()
		stream.write(u'A,B,C'.encode('utf-8'))
		stream.write(u'ő,ú,á'.encode('utf-8'))
		stream.write(u'é,ű,í'.encode('utf-8'))
		stream.seek(0)
		db = module.Database(stream)
		dct = {'database': db, 'document_template': Template('{% for entry in entries %}{{entry}}{% endfor %}'), 
		'entry_template': Template('{{A}}, {{B}}, {{C}}'), 'output': StringIO(), 'encoding': 'utf-8'}
		conf = module.Configuration(dct)
		document = conf.render_document()
		try:
			document.decode('utf-8')
		except Exception:
			self.fail('Could not decode string as UTF-8.')

	def test_output_rendered_in_html(self):
		stream = StringIO()
		stream.write(u'A,B,C'.encode('utf-8'))
		stream.write(u'ő,ú,á'.encode('utf-8'))
		stream.write(u'é,ű,í'.encode('utf-8'))
		stream.seek(0)
		db = module.Database(stream)
		dct = {'database': db, 'document_template': Template('{% for entry in entries %}{{entry}}{% endfor %}'), 
		'entry_template': Template('{{A}}, {{B}}, {{C}}'), 'output': StringIO(), 'encoding': 'html'}
		conf = module.Configuration(dct)
		document = conf.render_document()
		try:
			document.decode('ascii')
		except Exception:
			self.fail('Could not decode string as ascii.')

class TestResolver(ut.TestCase):
	def test_known_example(self):
		stream = StringIO()
		yaml.dump(dict(A=1, B=2), stream)
		stream.seek(0)

		resolver = module.Resolver(stream)
		self.assertEqual(resolver.resolve('A'), 1)
		self.assertEqual(resolver.resolve('B'), 2)

	def test_stream_has_to_be_dictionary(self):
		stream = StringIO()
		yaml.dump([1, 2, 3], stream)
		stream.seek(0)

		def callable():
			resolver = module.Resolver(stream)
		self.assertRaises(TypeError, callable)

	def test_missing_key_cannot_be_resolved(self):
		stream = StringIO()
		yaml.dump(dict(A=1, B=2), stream)
		stream.seek(0)

		resolver = module.Resolver(stream)
		def callable():
			resolver.resolve('C')
		self.assertRaises(KeyError, callable)

class TestFilter(ut.TestCase):
	def test_split(self):
		f = module.Filter()
		result = f.apply('split', 'a, b, c')
		self.assertListEqual(result, ['a', 'b', 'c'])

	def test_joint(self):
		f = module.Filter()
		result = f.apply('join', ['a', 'b', 'c'])
		self.assertEqual(result, 'a, b, c')

	def test_split_join(self):
		f = module.Filter()
		result = f.apply_all(['split', 'join'], 'a, b, c')
		self.assertEqual(result, 'a, b, c')

	def test_append(self):
		f = module.Filter()
		result = f.apply('append:4', '123')
		self.assertEqual(result, '1234')

	def test_substitute(self):
		f = module.Filter()
		stream = StringIO()
		yaml.dump(dict(b='B'), stream)
		stream.seek(0)

		resolver = module.Resolver(stream)
		self.assertEqual(f._filter_substitute('b', resolver), 'B')

	def test_missing_key_not_substituted(self):
		f = module.Filter()
		stream = StringIO()
		yaml.dump(dict(b='B'), stream)
		stream.seek(0)

		resolver = module.Resolver(stream)
		self.assertEqual(f._filter_substitute('c', resolver), 'c')

	def test_split_append_join(self):
		f = module.Filter()
		result = f.apply_all(['split', 'append:0', 'join'], 'a, b, c')
		self.assertEqual(result, 'a0, b0, c0')


if __name__ == '__main__':
    ut.main()
