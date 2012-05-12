import unittest
import confit
import sys

PY3 = sys.version_info[0] == 3

def _root(*sources):
    return confit.RootView(sources)

class SingleSourceTest(unittest.TestCase):
    def test_dict_access(self):
        config = _root({'foo': 'bar'})
        value = config['foo'].get()
        self.assertEqual(value, 'bar')

    def test_list_access(self):
        config = _root(['foo', 'bar'])
        value = config[1].get()
        self.assertEqual(value, 'bar')

    def test_nested_dict_list_access(self):
        config = _root({'foo': ['bar', 'baz']})
        value = config['foo'][1].get()
        self.assertEqual(value, 'baz')

    def test_nested_list_dict_access(self):
        config = _root([{'foo': 'bar'}, {'baz': 'qux'}])
        value = config[1]['baz'].get()
        self.assertEqual(value, 'qux')

    def test_missing_key(self):
        config = _root({'foo': 'bar'})
        with self.assertRaises(confit.NotFoundError):
            config['baz'].get()

    def test_missing_index(self):
        config = _root(['foo', 'bar'])
        with self.assertRaises(confit.NotFoundError):
            config[5].get()

    def test_dict_keys(self):
        config = _root({'foo': 'bar', 'baz': 'qux'})
        keys = config.keys()
        self.assertEqual(set(keys), set(['foo', 'baz']))

    def test_dict_values(self):
        config = _root({'foo': 'bar', 'baz': 'qux'})
        values = [value.get() for value in config.values()]
        self.assertEqual(set(values), set(['bar', 'qux']))

    def test_dict_items(self):
        config = _root({'foo': 'bar', 'baz': 'qux'})
        items = [(key, value.get()) for (key, value) in config.items()]
        self.assertEqual(set(items), set([('foo', 'bar'), ('baz', 'qux')]))

    def test_list_keys_error(self):
        config = _root(['foo', 'bar'])
        with self.assertRaises(confit.ConfigTypeError):
            config.keys()

    def test_dict_contents(self):
        config = _root({'foo': 'bar', 'baz': 'qux'})
        contents = config.all_contents()
        self.assertEqual(set(contents), set(['foo', 'baz']))

    def test_list_contents(self):
        config = _root(['foo', 'bar'])
        contents = config.all_contents()
        self.assertEqual(list(contents), ['foo', 'bar'])

    def test_int_contents(self):
        config = _root(2)
        with self.assertRaises(confit.ConfigTypeError):
            list(config.all_contents())

class TypeCheckTest(unittest.TestCase):
    def test_str_type_correct(self):
        config = _root({'foo': 'bar'})
        value = config['foo'].get(str)
        self.assertEqual(value, 'bar')

    def test_str_type_incorrect(self):
        config = _root({'foo': 2})
        with self.assertRaises(confit.ConfigTypeError):
            config['foo'].get(str)

    def test_int_type_correct(self):
        config = _root({'foo': 2})
        value = config['foo'].get(int)
        self.assertEqual(value, 2)

    def test_int_type_incorrect(self):
        config = _root({'foo': 'bar'})
        with self.assertRaises(confit.ConfigTypeError):
            config['foo'].get(int)

class ConverstionTest(unittest.TestCase):
    def test_str_conversion_from_str(self):
        config = _root({'foo': 'bar'})
        value = str(config['foo'])
        self.assertEqual(value, 'bar')

    def test_str_conversion_from_int(self):
        config = _root({'foo': 2})
        value = str(config['foo'])
        self.assertEqual(value, '2')

    def test_unicode_conversion_from_int(self):
        if not PY3:
            config = _root({'foo': 2})
            value = unicode(config['foo'])
            self.assertEqual(value, unicode('2'))

    def test_bool_conversion_from_bool(self):
        config = _root({'foo': True})
        value = bool(config['foo'])
        self.assertEqual(value, True)

    def test_bool_conversion_from_int(self):
        config = _root({'foo': 0})
        value = bool(config['foo'])
        self.assertEqual(value, False)

class NameTest(unittest.TestCase):
    def test_root_name(self):
        config = _root(None)
        name = config.name()
        self.assertEqual(name, 'root')

    def test_string_access_name(self):
        config = _root(None)
        name = config['foo'].name()
        self.assertEqual(name, "root['foo']")

    def test_int_access_name(self):
        config = _root(None)
        name = config[5].name()
        self.assertEqual(name, "root[5]")

    def test_nested_access_name(self):
        config = _root(None)
        name = config[5]['foo']['bar'][20].name()
        self.assertEqual(name, "root[5]['foo']['bar'][20]")

class MultipleSourceTest(unittest.TestCase):
    def test_dict_access_shadowed(self):
        config = _root({'foo': 'bar'}, {'foo': 'baz'})
        value = config['foo'].get()
        self.assertEqual(value, 'bar')

    def test_dict_access_fall_through(self):
        config = _root({'qux': 'bar'}, {'foo': 'baz'})
        value = config['foo'].get()
        self.assertEqual(value, 'baz')

    def test_dict_access_missing(self):
        config = _root({'qux': 'bar'}, {'foo': 'baz'})
        with self.assertRaises(confit.NotFoundError):
            config['fred'].get()

    def test_list_access_shadowed(self):
        config = _root(['a', 'b'], ['c', 'd', 'e'])
        value = config[1].get()
        self.assertEqual(value, 'b')

    def test_list_access_fall_through(self):
        config = _root(['a', 'b'], ['c', 'd', 'e'])
        value = config[2].get()
        self.assertEqual(value, 'e')

    def test_list_access_missing(self):
        config = _root(['a', 'b'], ['c', 'd', 'e'])
        with self.assertRaises(confit.NotFoundError):
            config[3].get()

    def test_access_dict_replaced(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'qux': 'fred'}})
        value = config['foo'].get()
        self.assertEqual(value, {'bar': 'baz'})

    def test_dict_keys_merged(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'qux': 'fred'}})
        keys = config['foo'].keys()
        self.assertEqual(set(keys), set(['bar', 'qux']))

    def test_dict_keys_replaced(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'bar': 'fred'}})
        keys = config['foo'].keys()
        self.assertEqual(list(keys), ['bar'])

    def test_dict_values_merged(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'qux': 'fred'}})
        values = [value.get() for value in config['foo'].values()]
        self.assertEqual(set(values), set(['baz', 'fred']))

    def test_dict_values_replaced(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'bar': 'fred'}})
        values = [value.get() for value in config['foo'].values()]
        self.assertEqual(list(values), ['baz'])

    def test_dict_items_merged(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'qux': 'fred'}})
        items = [(key, value.get()) for (key, value) in config['foo'].items()]
        self.assertEqual(set(items), set([('bar', 'baz'), ('qux', 'fred')]))

    def test_dict_items_replaced(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'bar': 'fred'}})
        items = [(key, value.get()) for (key, value) in config['foo'].items()]
        self.assertEqual(list(items), [('bar', 'baz')])

    def test_dict_contents_concatenated(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'qux': 'fred'}})
        contents = config['foo'].all_contents()
        self.assertEqual(set(contents), set(['bar', 'qux']))

    def test_dict_contents_concatenated_not_replaced(self):
        config = _root({'foo': {'bar': 'baz'}}, {'foo': {'bar': 'fred'}})
        contents = config['foo'].all_contents()
        self.assertEqual(list(contents), ['bar', 'bar'])

    def test_list_contents_concatenated(self):
        config = _root({'foo': ['bar', 'baz']}, {'foo': ['qux', 'fred']})
        contents = config['foo'].all_contents()
        self.assertEqual(list(contents), ['bar', 'baz', 'qux', 'fred'])

    def test_int_contents_error(self):
        config = _root({'foo': ['bar', 'baz']}, {'foo': 5})
        with self.assertRaises(confit.ConfigTypeError):
            list(config['foo'].all_contents())

    def test_list_and_dict_contents_concatenated(self):
        config = _root({'foo': ['bar', 'baz']}, {'foo': {'qux': 'fred'}})
        contents = config['foo'].all_contents()
        self.assertEqual(list(contents), ['bar', 'baz', 'qux'])

