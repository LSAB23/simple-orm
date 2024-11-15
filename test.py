from fields import  BooleanField, IntField,Char, ForeignKey
from models import Model
import unittest

class database1(Model):
    test_int = IntField(max_length=100, primary_key=True)
    test_char = Char(max_length=100)
    test_bool = BooleanField()

class database2(Model):
    test_foriegn= ForeignKey(model=database1)
    db_char = Char(max_length=100)
    db_int = IntField()


# added the alphabets infront to make them run in other
class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db1 = database1
        cls.db2 = database2
        
    
    #migration
    def test_amigrate(self):
        one = self.db1().migrate()
        two = self.db2().migrate()

        self.assertIsNone(one, 'migrate works')
        self.assertIsNone(two, 'migrate works')
    
    # save or insert operation
    def test_bsave(self):
        one = self.db1(test_int= None,test_char='db1 test case 1', test_bool=True).save()
        two = self.db2(test_foriegn=1,db_char='db2 test case 1', db_int=12).save()

        three = self.db1(test_int=None,test_char='db1 test case 2', test_bool=True).save()
        four = self.db2(test_foriegn=2,db_char='db2 test case 2', db_int=10).save()
        
        self.assertIsNone(one)
        self.assertIsNone(two)
        self.assertIsNone(three)
        self.assertIsNone(four)
    
    # filter and if save work
    def test_cfilter(self):
        filter_for_one :list[dict]= self.db1().filter(test_int=1).all() # type: ignore
        filter_for_two :list[dict]= self.db1().filter(test_int=2).all() # type: ignore

        self.assertTrue(filter_for_one[0], {'test_int': 1, 'test_char': 'db1 test case 1', 'test_bool': 'True'})
        self.assertEqual(filter_for_two[0], {'test_int': 2, 'test_char': 'db1 test case 2', 'test_bool': 'True'})
    
    #gets specific item with id or any other unique field
    def text_dexact(self):
        get_one = self.db1().filter(test_int=1).exact()
        self.assertEqual(get_one, {'test_int': 1, 'test_char': 'db1 test case 1', 'test_bool': 'True'})
    
    # update function 
    def test_eupdate(self):
        self.db1(test_char='hello world', test_bool=False).update(test_int=1)
        result = self.db1().filter(test_int=1).exact()
        self.assertEqual(result, [{'test_int': 1, 'test_char': 'hello world', 'test_bool': 'False'}])
    
    # delete base on kwargs given
    def test_fdelete(self):
        self.db1().delete(test_char='db1 test case 1')
        self.assertFalse(self.db1().filter(test_char='db1 test case 1').all())
    
    # get all the fields you put in fields
    def test_gget(self):
        self.assertEqual(self.db1().get('test_int','test_char')[0], {'test_int': 1, 'test_char': 'hello world'})
    
    # filter delete
    def test_hfilter_delete(self):
        instance = self.db1().filter(test_int=1)
        instance.delete()
        self.assertFalse(instance.all())
    
# join it was causing trace errors
class Join(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db1 = database1
        cls.db2 = database2
        
        cls.db1().migrate()
        cls.db2().migrate()

        cls.db1(test_int= None,test_char='db1 test case 1', test_bool=True).save()
        cls.db2(test_foriegn=1,db_char='db2 test case 1', db_int=12).save()

        cls.db1(test_int=None,test_char='db1 test case 2', test_bool=True).save()
        cls.db2(test_foriegn=2,db_char='db2 test case 2', db_int=10).save()
    
    
    def test_ijoin(self):
        result = self.db2().filter(test_foriegn=2).join()
        self.assertEqual(result, [(2, 'db2 test case 2', 10, 2, 'db1 test case 2', 'True')])
    #  delete db for the test        


# couldn't delete the db afterwards but this prevent the traceback error for some weird reason
class Delete(unittest.TestCase):
    def test_zdeletedb(self):
        import pathlib
        print(pathlib.Path().absolute())


if __name__ == '__main__':
    unittest.main()
    
