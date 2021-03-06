""" Test the write functions of Dynamo """
from __future__ import unicode_literals

from mock import MagicMock, call, ANY, patch
from six.moves import xrange as _xrange  # pylint: disable=F0401

from . import BaseSystemTest, is_number
from dynamo3 import (STRING, NUMBER, DynamoKey, LocalIndex, GlobalIndex, Table,
                     Throughput, ItemUpdate, ALL_NEW, ALL_OLD, TOTAL,
                     CheckFailed, IndexUpdate)
from dynamo3.batch import BatchWriter
from dynamo3.result import Capacity


class TestCreate(BaseSystemTest):

    """ Test creating a table """

    def test_create_hash_table(self):
        """ Create a table with just a hash key """
        hash_key = DynamoKey('id', data_type=STRING)
        table = Table('foobar', hash_key)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_hash_range_table(self):
        """ Create a table with a hash and range key """
        hash_key = DynamoKey('id', data_type=STRING)
        range_key = DynamoKey('num', data_type=NUMBER)
        table = Table('foobar', hash_key, range_key)
        self.dynamo.create_table('foobar', hash_key, range_key)
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_local_index(self):
        """ Create a table with a local index """
        hash_key = DynamoKey('id', data_type=STRING)
        range_key = DynamoKey('num', data_type=NUMBER)
        index_field = DynamoKey('name')
        index = LocalIndex.all('name-index', index_field)
        table = Table('foobar', hash_key, range_key, [index])
        self.dynamo.create_table(
            'foobar', hash_key, range_key, indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_local_keys_index(self):
        """ Create a table with a local KeysOnly index """
        hash_key = DynamoKey('id', data_type=STRING)
        range_key = DynamoKey('num', data_type=NUMBER)
        index_field = DynamoKey('name')
        index = LocalIndex.keys('name-index', index_field)
        table = Table('foobar', hash_key, range_key, [index])
        self.dynamo.create_table(
            'foobar', hash_key, range_key, indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_local_includes_index(self):
        """ Create a table with a local Includes index """
        hash_key = DynamoKey('id', data_type=STRING)
        range_key = DynamoKey('num', data_type=NUMBER)
        index_field = DynamoKey('name')
        index = LocalIndex.include('name-index', index_field,
                                   includes=['foo', 'bar'])
        table = Table('foobar', hash_key, range_key, [index])
        self.dynamo.create_table(
            'foobar', hash_key, range_key, indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_global_index(self):
        """ Create a table with a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        table = Table('foobar', hash_key, global_indexes=[index])
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_global_keys_index(self):
        """ Create a table with a global KeysOnly index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.keys('name-index', index_field)
        table = Table('foobar', hash_key, global_indexes=[index])
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_global_includes_index(self):
        """ Create a table with a global Includes index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.include(
            'name-index', index_field, includes=['foo', 'bar'])
        table = Table('foobar', hash_key, global_indexes=[index])
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_global_hash_range_index(self):
        """ Create a global index with a hash and range key """
        hash_key = DynamoKey('id', data_type=STRING)
        index_hash = DynamoKey('foo')
        index_range = DynamoKey('bar')
        index = GlobalIndex.all('foo-index', index_hash, index_range)
        table = Table('foobar', hash_key, global_indexes=[index])
        self.dynamo.create_table('foobar', hash_key, global_indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_table_throughput(self):
        """ Create a table and set throughput """
        hash_key = DynamoKey('id', data_type=STRING)
        throughput = Throughput(8, 2)
        table = Table('foobar', hash_key, throughput=throughput)
        self.dynamo.create_table(
            'foobar', hash_key=hash_key, throughput=throughput)
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)

    def test_create_global_index_throughput(self):
        """ Create a table and set throughput on global index """
        hash_key = DynamoKey('id', data_type=STRING)
        throughput = Throughput(8, 2)
        index_field = DynamoKey('name')
        index = GlobalIndex.all(
            'name-index', index_field, throughput=throughput)
        table = Table('foobar', hash_key, global_indexes=[index])
        self.dynamo.create_table(
            'foobar', hash_key=hash_key, global_indexes=[index])
        desc = self.dynamo.describe_table('foobar')
        self.assertEqual(desc, table)


class TestUpdateTable(BaseSystemTest):

    """ Test updating table/index throughput """

    def test_update_table_throughput(self):
        """ Update the table throughput """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        tp = Throughput(2, 1)
        self.dynamo.update_table('foobar', throughput=tp)
        table = self.dynamo.describe_table('foobar')
        self.assertEqual(table.throughput, tp)

    def test_update_global_index_throughput_old(self):
        """ Update throughput on a global index OLD API """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 global_indexes=[index])
        tp = Throughput(2, 1)
        self.dynamo.update_table('foobar', global_indexes={'name-index': tp})
        table = self.dynamo.describe_table('foobar')
        self.assertEqual(table.global_indexes[0].throughput, tp)

    def test_update_multiple_throughputs(self):
        """ Update table and global index throughputs """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 global_indexes=[index])
        tp = Throughput(2, 1)
        self.dynamo.update_table('foobar', throughput=tp,
                                 global_indexes={'name-index': tp})
        table = self.dynamo.describe_table('foobar')
        self.assertEqual(table.throughput, tp)
        self.assertEqual(table.global_indexes[0].throughput, tp)

    def test_update_index_throughput(self):
        """ Update the throughput on a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 global_indexes=[index])
        tp = Throughput(2, 1)
        self.dynamo.update_table('foobar', index_updates=[
            IndexUpdate.update('name-index', tp)])
        table = self.dynamo.describe_table('foobar')
        self.assertEqual(table.global_indexes[0].throughput, tp)

    def test_delete_index(self):
        """ Delete a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field)
        self.dynamo.create_table('foobar', hash_key=hash_key,
                                 global_indexes=[index])
        self.dynamo.update_table('foobar', index_updates=[
            IndexUpdate.delete('name-index')])
        table = self.dynamo.describe_table('foobar')
        self.assertTrue(len(table.global_indexes) == 0 or
                        table.global_indexes[0].index_status == 'DELETING')

    def test_create_index(self):
        """ Create a global index """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        index_field = DynamoKey('name')
        index = GlobalIndex.all('name-index', index_field, hash_key)
        self.dynamo.update_table('foobar', index_updates=[
            IndexUpdate.create(index)])
        table = self.dynamo.describe_table('foobar')
        self.assertEqual(len(table.global_indexes), 1)

    def test_index_update_equality(self):
        """ IndexUpdates should have sane == behavior """
        self.assertEqual(IndexUpdate.delete('foo'), IndexUpdate.delete('foo'))
        collection = set([IndexUpdate.delete('foo')])
        self.assertIn(IndexUpdate.delete('foo'), collection)
        self.assertNotEqual(IndexUpdate.delete('foo'),
                            IndexUpdate.delete('bar'))


class TestBatchWrite(BaseSystemTest):

    """ Test the batch write operation """

    def test_write_items(self):
        """ Batch write items to table """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        with self.dynamo.batch_write('foobar') as batch:
            batch.put({'id': 'a'})
        ret = list(self.dynamo.scan('foobar'))
        self.assertItemsEqual(ret, [{'id': 'a'}])

    def test_delete_items(self):
        """ Batch write can delete items from table """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        with self.dynamo.batch_write('foobar') as batch:
            batch.put({'id': 'a'})
            batch.put({'id': 'b'})
        with self.dynamo.batch_write('foobar') as batch:
            batch.delete({'id': 'b'})
        ret = list(self.dynamo.scan('foobar'))
        self.assertItemsEqual(ret, [{'id': 'a'}])

    def test_write_many(self):
        """ Can batch write arbitrary numbers of items """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(50):
                batch.put({'id': str(i)})
        count = self.dynamo.scan('foobar', count=True)
        self.assertEqual(count, 50)
        with self.dynamo.batch_write('foobar') as batch:
            for i in _xrange(50):
                batch.delete({'id': str(i)})
        count = self.dynamo.scan('foobar', count=True)
        self.assertEqual(count, 0)

    def test_write_converts_none(self):
        """ Write operation converts None values to a DELETE """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        with self.dynamo.batch_write('foobar') as batch:
            batch.put({'id': 'a', 'foo': None})
        ret = list(self.dynamo.scan('foobar'))
        self.assertItemsEqual(ret, [{'id': 'a'}])

    def test_handle_unprocessed(self):
        """ Retry all unprocessed items """
        conn = MagicMock()
        writer = BatchWriter(conn, 'foo')
        key1, key2 = object(), object()
        unprocessed = [[key1], [key2], []]
        conn.call.side_effect = lambda *_, **__: {
            'UnprocessedItems': {
                'foo': unprocessed.pop(0),
            }
        }
        with writer:
            writer.put({'id': 'a'})
        # Should insert the first item, and then the two sets we marked as
        # unprocessed
        self.assertEqual(len(conn.call.mock_calls), 3)
        kwargs = {
            'RequestItems': {
                'foo': [key1],
            },
            'ReturnConsumedCapacity': ANY,
            'ReturnItemCollectionMetrics': ANY,
        }
        self.assertEqual(conn.call.mock_calls[1],
                         call('batch_write_item', **kwargs))
        kwargs['RequestItems']['foo'][0] = key2
        self.assertEqual(conn.call.mock_calls[2],
                         call('batch_write_item', **kwargs))

    def test_exc_aborts(self):
        """ Exception during a write will not flush data """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        try:
            with self.dynamo.batch_write('foobar') as batch:
                batch.put({'id': 'a'})
                raise Exception
        except Exception:
            pass
        ret = list(self.dynamo.scan('foobar'))
        self.assertEqual(len(ret), 0)

    def test_capacity(self):
        """ Can return consumed capacity """
        ret = {
            'Responses': {
                'foo': [],
            },
            'ConsumedCapacity': [{
                'TableName': 'foobar',
                'CapacityUnits': 3,
                'Table': {
                    'CapacityUnits': 1,
                },
                'LocalSecondaryIndexes': {
                    'l-index': {
                        'CapacityUnits': 1,
                    },
                },
                'GlobalSecondaryIndexes': {
                    'g-index': {
                        'CapacityUnits': 1,
                    },
                },
            }],
        }
        with patch.object(self.dynamo.client, 'batch_write_item', return_value=ret):
            batch = self.dynamo.batch_write('foobar',
                                            return_capacity='INDEXES')
            with batch:
                batch.put({'id': 'a'})
        self.assertEqual(batch.consumed_capacity.total, Capacity(0, 3))


class TestUpdateItem(BaseSystemTest):

    """ Test the UpdateItem call """

    def make_table(self):
        """ Convenience method for creating a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_update_field(self):
        """ Update an item field """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.update_item('foobar', {'id': 'a'},
                                [ItemUpdate.put('foo', 'bar')])
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': 'bar'})

    def test_atomic_add_num(self):
        """ Update can atomically add to a number """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.update_item('foobar', {'id': 'a'},
                                [ItemUpdate.add('foo', 1)])
        self.dynamo.update_item('foobar', {'id': 'a'},
                                [ItemUpdate.add('foo', 2)])
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': 3})

    def test_atomic_add_set(self):
        """ Update can atomically add to a set """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.update_item('foobar', {'id': 'a'},
                                [ItemUpdate.add('foo', set([1]))])
        self.dynamo.update_item('foobar', {'id': 'a'},
                                [ItemUpdate.add('foo', set([1, 2]))])
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': set([1, 2])})

    def test_delete_field(self):
        """ Update can delete fields from an item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        self.dynamo.update_item('foobar', {'id': 'a'},
                                [ItemUpdate.delete('foo')])
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a'})

    def test_return_item(self):
        """ Update can return the updated item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.update_item('foobar', {'id': 'a'},
                                      [ItemUpdate.put('foo', 'bar')],
                                      returns=ALL_NEW)
        self.assertEqual(ret, {'id': 'a', 'foo': 'bar'})

    def test_return_metadata(self):
        """ The Update return value contains capacity metadata """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.update_item('foobar', {'id': 'a'},
                                      [ItemUpdate.put('foo', 'bar')],
                                      returns=ALL_NEW,
                                      return_capacity=TOTAL)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_expect_not_exists_deprecated(self):
        """ Update can expect a field to not exist """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        update = ItemUpdate.put('foo', 'baz', expected=None)
        with self.assertRaises(CheckFailed):
            self.dynamo.update_item('foobar', {'id': 'a'}, [update])

    def test_expect_field_deprecated(self):
        """ Update can expect a field to have a value """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        update = ItemUpdate.put('foo', 'baz', expected='wat')
        with self.assertRaises(CheckFailed):
            self.dynamo.update_item('foobar', {'id': 'a'}, [update])

    def test_expect_condition(self):
        """ Update can expect a field to meet a condition """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        update = ItemUpdate.put('foo', 10, lt=5)
        with self.assertRaises(CheckFailed):
            self.dynamo.update_item('foobar', {'id': 'a'}, [update])

    def test_expect_condition_or(self):
        """ Expected conditionals can be OR'd together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        update = ItemUpdate.put('foo', 10, lt=5)
        self.dynamo.update_item('foobar', {'id': 'a'}, [update],
                                expect_or=True, baz__null=True)

    def test_expect_dupe_fail(self):
        """ Update cannot expect a field to meet multiple constraints """
        self.make_table()
        with self.assertRaises(ValueError):
            update = ItemUpdate.put('foo', 10, lt=5, gt=1)

    def test_expect_dupe_fail2(self):
        """ Update cannot expect a field to meet multiple constraints """
        self.make_table()
        update = ItemUpdate.put('foo', 10, lt=5)
        with self.assertRaises(ValueError):
            self.dynamo.update_item('foobar', {'id': 'a'}, [update], foo__gt=1)

    def test_write_converts_none(self):
        """ Write operation converts None values to a DELETE """
        hash_key = DynamoKey('id', data_type=STRING)
        self.dynamo.create_table('foobar', hash_key=hash_key)
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        update = ItemUpdate.put('foo', None)
        self.dynamo.update_item('foobar', {'id': 'a'}, [update])
        ret = list(self.dynamo.scan('foobar'))
        self.assertItemsEqual(ret, [{'id': 'a'}])

    def test_condition_converts_eq_null(self):
        """ Conditional converts eq=None to null=True """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        update = ItemUpdate.put('foo', set([1, 2]), eq=set())
        self.dynamo.update_item('foobar', {'id': 'a'}, [update])
        update = ItemUpdate.put('foo', set([2]), eq=set())
        with self.assertRaises(CheckFailed):
            self.dynamo.update_item('foobar', {'id': 'a'}, [update])

    def test_write_add_require_value(self):
        """ Doing an ADD requires a non-null value """
        with self.assertRaises(ValueError):
            ItemUpdate.add('foo', None)

    def test_item_update_eq(self):
        """ ItemUpdates should be equal """
        a, b = ItemUpdate.put('foo', 'bar'), ItemUpdate.put('foo', 'bar')
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))
        self.assertFalse(a != b)


class TestUpdateItem2(BaseSystemTest):

    """ Test the new UpdateItem API """

    def make_table(self):
        """ Convenience method for creating a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_update_field(self):
        """ Update an item field """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'SET foo = :bar',
                                 bar='bar')
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': 'bar'})

    def test_atomic_add_num(self):
        """ Update can atomically add to a number """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'ADD foo :foo', foo=1)
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'ADD foo :foo', foo=2)
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': 3})

    def test_atomic_add_set(self):
        """ Update can atomically add to a set """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'ADD foo :foo',
                                 foo=set([1]))
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'ADD foo :foo',
                                 foo=set([1, 2]))
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': set([1, 2])})

    def test_delete_field(self):
        """ Update can delete fields from an item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'REMOVE foo')
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a'})

    def test_return_item(self):
        """ Update can return the updated item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.update_item2('foobar', {'id': 'a'}, 'SET foo = :foo',
                                       returns=ALL_NEW, foo='bar')
        self.assertEqual(ret, {'id': 'a', 'foo': 'bar'})

    def test_return_metadata(self):
        """ The Update return value contains capacity metadata """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.update_item2('foobar', {'id': 'a'}, 'SET foo = :foo',
                                       returns=ALL_NEW, return_capacity=TOTAL,
                                       foo='bar')
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_expect_condition(self):
        """ Update can expect a field to meet a condition """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        with self.assertRaises(CheckFailed):
            self.dynamo.update_item2('foobar', {'id': 'a'}, 'SET foo = :foo',
                                     condition='foo < :max', foo=10, max=5)

    def test_expect_condition_or(self):
        """ Expected conditionals can be OR'd together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        self.dynamo.update_item2(
            'foobar', {'id': 'a'}, 'SET foo = :foo',
            condition='foo < :max OR NOT attribute_exists(baz)', foo=10, max=5)

    def test_expression_values(self):
        """ Can pass in expression values directly """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        self.dynamo.update_item2('foobar', {'id': 'a'}, 'SET #f = :foo',
                                 alias={'#f': 'foo'}, expr_values={':foo': 10})
        item = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(item, {'id': 'a', 'foo': 10})


class TestPutItem(BaseSystemTest):

    """ Tests for PutItem """

    def make_table(self):
        """ Convenience method for creating a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_new_item(self):
        """ Can Put new item into table """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(ret, {'id': 'a'})

    def test_overwrite_item(self):
        """ Can overwrite an existing item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'baz'})
        ret = self.dynamo.get_item('foobar', {'id': 'a'})
        self.assertEqual(ret, {'id': 'a', 'foo': 'baz'})

    def test_expect_not_exists_deprecated(self):
        """ Can expect a field to not exist """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        with self.assertRaises(CheckFailed):
            self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'baz'},
                                 expected={'foo': None})

    def test_expect_field_deprecated(self):
        """ Can expect a field to have a value """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        with self.assertRaises(CheckFailed):
            self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'baz'},
                                 expected={'foo': 'bar'})

    def test_expect_condition(self):
        """ Put can expect a field to meet a condition """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        with self.assertRaises(CheckFailed):
            self.dynamo.put_item('foobar', {'id': 'a', 'foo': 13},
                                 foo__lt=4)

    def test_expect_condition_or(self):
        """ Expected conditionals can be OR'd together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 13},
                             expect_or=True, foo__lt=4, baz__null=True)

    def test_return_item(self):
        """ PutItem can return the item that was Put """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.put_item('foobar', {'id': 'a'}, returns=ALL_OLD)
        self.assertEqual(ret, {'id': 'a'})

    def test_return_capacity(self):
        """ PutItem can return the consumed capacity """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.put_item('foobar', {'id': 'a'},
                                   returns=ALL_OLD,
                                   return_capacity=TOTAL)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))


class TestPutItem2(BaseSystemTest):

    """ Tests for new PutItem API """

    def make_table(self):
        """ Convenience method for creating a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_new_item(self):
        """ Can Put new item into table """
        self.make_table()
        self.dynamo.put_item2('foobar', {'id': 'a'})
        ret = list(self.dynamo.scan('foobar'))[0]
        self.assertEqual(ret, {'id': 'a'})

    def test_overwrite_item(self):
        """ Can overwrite an existing item """
        self.make_table()
        self.dynamo.put_item2('foobar', {'id': 'a', 'foo': 'bar'})
        self.dynamo.put_item2('foobar', {'id': 'a', 'foo': 'baz'})
        ret = self.dynamo.get_item('foobar', {'id': 'a'})
        self.assertEqual(ret, {'id': 'a', 'foo': 'baz'})

    def test_expect_condition(self):
        """ Put can expect a field to meet a condition """
        self.make_table()
        self.dynamo.put_item2('foobar', {'id': 'a', 'foo': 5})
        with self.assertRaises(CheckFailed):
            self.dynamo.put_item2('foobar', {'id': 'a', 'foo': 13},
                                  condition='#f < :v', alias={'#f': 'foo'},
                                  v=4)

    def test_expect_condition_or(self):
        """ Expected conditionals can be OR'd together """
        self.make_table()
        self.dynamo.put_item2('foobar', {'id': 'a', 'foo': 5})
        self.dynamo.put_item2('foobar', {'id': 'a', 'foo': 13},
                              condition='foo < :v OR attribute_not_exists(baz)',
                              v=4)

    def test_return_item(self):
        """ PutItem can return the item that was Put """
        self.make_table()
        self.dynamo.put_item2('foobar', {'id': 'a'})
        ret = self.dynamo.put_item2('foobar', {'id': 'a'}, returns=ALL_OLD)
        self.assertEqual(ret, {'id': 'a'})

    def test_return_capacity(self):
        """ PutItem can return the consumed capacity """
        self.make_table()
        self.dynamo.put_item2('foobar', {'id': 'a'})
        ret = self.dynamo.put_item2('foobar', {'id': 'a'},
                                    returns=ALL_OLD,
                                    return_capacity=TOTAL)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))


class TestDeleteItem(BaseSystemTest):

    """ Tests for DeleteItem """

    def make_table(self):
        """ Convenience method for creating a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_delete(self):
        """ Delete an item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.delete_item('foobar', {'id': 'a'})
        num = self.dynamo.scan('foobar', count=True)
        self.assertEqual(num, 0)

    def test_return_item(self):
        """ Delete can return the deleted item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        ret = self.dynamo.delete_item('foobar', {'id': 'a'}, returns=ALL_OLD)
        self.assertEqual(ret, {'id': 'a', 'foo': 'bar'})

    def test_return_metadata(self):
        """ The Delete return value contains capacity metadata """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.delete_item('foobar', {'id': 'a'},
                                      returns=ALL_OLD,
                                      return_capacity=TOTAL)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_expect_not_exists_deprecated(self):
        """ Delete can expect a field to not exist """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        with self.assertRaises(CheckFailed):
            self.dynamo.delete_item('foobar', {'id': 'a'}, {'foo': None})

    def test_expect_field_deprecated(self):
        """ Delete can expect a field to have a value """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        with self.assertRaises(CheckFailed):
            self.dynamo.delete_item('foobar', {'id': 'a'}, {'foo': 'baz'})

    def test_expect_condition(self):
        """ Delete can expect a field to meet a condition """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        with self.assertRaises(CheckFailed):
            self.dynamo.delete_item('foobar', {'id': 'a'}, foo__lt=4)

    def test_expect_condition_or(self):
        """ Expected conditionals can be OR'd together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        self.dynamo.delete_item('foobar', {'id': 'a'}, expect_or=True,
                                foo__lt=4, baz__null=True)


class TestDeleteItem2(BaseSystemTest):

    """ Tests for the new DeleteItem API """

    def make_table(self):
        """ Convenience method for creating a table """
        hash_key = DynamoKey('id')
        self.dynamo.create_table('foobar', hash_key=hash_key)

    def test_delete(self):
        """ Delete an item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        self.dynamo.delete_item2('foobar', {'id': 'a'})
        num = self.dynamo.scan('foobar', count=True)
        self.assertEqual(num, 0)

    def test_return_item(self):
        """ Delete can return the deleted item """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        ret = self.dynamo.delete_item2('foobar', {'id': 'a'}, returns=ALL_OLD)
        self.assertEqual(ret, {'id': 'a', 'foo': 'bar'})

    def test_return_metadata(self):
        """ The Delete return value contains capacity metadata """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a'})
        ret = self.dynamo.delete_item2('foobar', {'id': 'a'},
                                       returns=ALL_OLD,
                                       return_capacity=TOTAL)
        self.assertTrue(is_number(ret.capacity))
        self.assertTrue(is_number(ret.table_capacity))
        self.assertTrue(isinstance(ret.indexes, dict))
        self.assertTrue(isinstance(ret.global_indexes, dict))

    def test_expect_not_exists_deprecated(self):
        """ Delete can expect a field to not exist """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        with self.assertRaises(CheckFailed):
            self.dynamo.delete_item2('foobar', {'id': 'a'},
                                     condition='NOT attribute_exists(foo)')

    def test_expect_field_deprecated(self):
        """ Delete can expect a field to have a value """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 'bar'})
        with self.assertRaises(CheckFailed):
            self.dynamo.delete_item2('foobar', {'id': 'a'},
                                     condition='#f = :foo',
                                     alias={'#f': 'foo'}, foo='baz')

    def test_expect_condition(self):
        """ Delete can expect a field to meet a condition """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        with self.assertRaises(CheckFailed):
            self.dynamo.delete_item2('foobar', {'id': 'a'},
                                     condition='foo < :low',
                                     expr_values={':low': 4})

    def test_expect_condition_or(self):
        """ Expected conditionals can be OR'd together """
        self.make_table()
        self.dynamo.put_item('foobar', {'id': 'a', 'foo': 5})
        self.dynamo.delete_item2(
            'foobar', {'id': 'a'},
            condition='foo < :foo OR NOT attribute_exists(baz)', foo=4)
