from functools import lru_cache
from itertools import zip_longest
from typing import Any
from .fields import  Field, IntField,Char,BooleanField, ForeignKey
from .creation import execute_query
from .error import ValidationError,FieldDoNotExist,MustBeOne,NoForeignKey

fields_list = [type(Char()),type(IntField()),type(BooleanField()),type(ForeignKey()) ]
class ModelMeta(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        super_new = super().__new__
        
        # excluding the parent model class itself in the initialization
        parents = [b for b in bases if isinstance(b, ModelMeta)]
        if not parents:
            super_new(cls,name,bases,attrs, **kwargs)

        
        module = attrs.pop("__module__")
        new_attrs = {"__module__": module}
        fields = {}

        # create a new attrs and using variable names as column names if name was not given and a new field dict
        for key,value in attrs.items():
            if type(value) in fields_list:
                if value.name: 
                    value = value
                else:
                    value.name=key
                
                fields[key] = value
                new_attrs[key] = value
            if callable(value):
                new_attrs[key] = value
        new_class = super_new(cls,name,bases,new_attrs,**kwargs)
        # adding fields as an attribute
        setattr(new_class, 'fields',fields)
        

        return new_class
        

class Model(metaclass=ModelMeta):
    def __init__(self, **kwargs) -> None:
        self.kwargs :dict= kwargs
        self.fields :dict = self.fields
        self.name :str = self.__class__.__name__
        self.main_query :str|None = None

    
    def migrate(self) -> None:
        field_query :str = ''
        foriegn_query :str= ''
        # get the query string for every field and add it to the final migration query
        for name,value in self.fields.items():
            value :Field = value
            table_name,type = value.new_table_query()
            if value._is_foreign_key():
                foriegn_query+=table_name
                foriegn_query+=f'{type}'
            else:
                field_query+=table_name
                field_query+=f'{type}'


        # remove the last comma from the query
        field_query :str= field_query + foriegn_query
        query :str=f"CREATE TABLE IF NOT EXISTS '{self.name}' ({field_query[:-1]})"
        # print(query, 'migrate query')
        execute_query(query)
        self.main_query = query

        return
    
    def primary_key(self) -> str|bool:
        for key,field in self.fields.items():
            if field._is_primary_key():
                return field.name
        return False
    
    def foreign_key(self) -> str|bool:
        for key,field in self.fields.items():
            if field._is_foreign_key():
                return field.name
        return False

    def save(self) -> None:
        to_save :list =list(zip_longest(self.fields,self.kwargs))
        
        values :str = ''
        for key,value in to_save:
            if value:
                value :Any= self.kwargs.get(value)
                            
                _value :Field = self.fields.get(key) # type: ignore , get the field instance

                if _value:
                    if _value.check(value) and not _value._is_primary_key() and not _value._is_foreign_key():
                        values+=(f'"{value}",')
                        

                    else:
                        # did this because it was causing errors if checking the validity during autoincrement 
                        if _value._is_primary_key():
                            continue
                        if _value._is_foreign_key():
                            values+=(f'"{value}",')
                            continue
                        else:
                            raise ValidationError(f'{value} faild the validation, {key} should be a {_value.__class__.__name__}')
            
        values = values[:-1]
        _fields = [_ if not value._is_primary_key() else '' for _,value in self.fields.items()]
        if '' in _fields:
            _fields.pop(_fields.index(''))

        query =f' INSERT INTO {self.name}{tuple(_fields)} VALUES({values})'
        # print(query, 'insert or save query')
        execute_query(query)
        self.main_query = query
        return
    def update(self, **kwargs) -> None:
        '''
        Just type what update in the main class and put the key primary or unique key in the update func 
        EG:
        Customer column
        id :int
        user: char
        customer(user=New_user_name).update(id=1)
        '''

        if len(kwargs) != 1:
            raise MustBeOne(f'{kwargs} should be the id only')
        
        self._validate(kwargs)
        self._validate(self.kwargs)
        id = list(kwargs.keys())[0]
        for _key,_value in self.kwargs.items():
            query :str= f'UPDATE {self.name} SET {_key} = "{_value}" WHERE {id}={kwargs.get(id)}'
            # print(query, 'update', self.name)
            execute_query(query)
            self.main_query = query

        return
    
    def delete(self, **kwargs) -> None:
        '''
        For only deletinng exact, to filter and delete use the filter(**kwargs).delete()
        '''
        self._validate(kwargs)
        for _key,_value in kwargs.items():
            query :str = f' DELETE FROM {self.name} WHERE {_key} = "{_value}"'
            # print(query, 'delete')
            execute_query(query)
            self.main_query = query

        return 

    def _validate(self, kwargs):
        for key,value in kwargs.items():
            field_exist :Field|None= self.fields.get(key)
            if not field_exist:
                raise FieldDoNotExist(f'"{key}" field do not exist you can use {self.fields.keys()}')
            check = field_exist.check(value)
            if not check:
                raise ValidationError(f'"{value}" faild the validation, "{key}" field should be a {field_exist.__class__.__name__} or check the lenght you can also change the lenght')
            return True
    
    @lru_cache
    def get(self, *args, limit :int|None=None) -> list[dict]:
        fields :str= ''
        for field in args:
            if field in self.fields.keys():
                fields+= f'{field},'
            else:
                raise FieldDoNotExist(f'"{field}" field do not exist you can use {self.fields.keys()}')
        query = f' SELECT {fields[:-1]} FROM {self.name}'
        if limit:
            query+= f' LIMIT {limit}'
        # print(query, 'get')
        self.main_query = query
        
        

        return self.to_dict(query,args)
    
    def to_dict(self, query, args):
        _result :list= []
        for result in execute_query(query).fetchall():
            _result.append(dict(zip(args,result)))
        return _result
    
    def filter(self, LIMIT :int|None=None,**kwargs):
        return self._filter(user_input=kwargs, main=self, LIMIT=LIMIT)
    
    class _filter:
        def __init__(self,LIMIT :int|None=None,**kwargs) -> None:
            
            self.kwargs :dict= kwargs
            self.main :Model= kwargs['main']
            self.user_input = self.kwargs['user_input']
            self.limit = LIMIT
            
            

            self.field = tuple(self.user_input.keys()) # type: ignore
            _query = ''
            for key,value in self.user_input.items():
                _query += f'{key} LIKE "%{value}%" or '
            if LIMIT:
                self.query = f' * FROM {self.main.name} WHERE {_query[:-3]} LIMIT {LIMIT}'
            else:
                self.query = f' * FROM {self.main.name} WHERE {_query[:-3]}'
                

            
        def all(self) -> list[dict]|None:
            _query = 'SELECT ' + self.query
            # print(_query)
            self.main_query = _query
            return self.main.to_dict(_query,self.main.fields.keys())
        
        def exact(self) -> list[dict]:
            
            _query = f'SELECT * FROM {self.main.name} WHERE'
            for key,value in self.user_input.items():
                _query += f' {key} = "{value}" and'
            _query = _query[:-3]
            if self.limit:
                _query+=f' LIMIT {self.limit}'
            self.main_query = _query
            return self.main.to_dict(_query,self.main.fields.keys())
        
        def delete(self):
            _query = f'DELETE ' + self.query.replace('*','').replace(f'LIMIT {self.limit}','')
            # print(_query)
            execute_query(_query)
            self.main_query = _query
            return
        
        def join_field(self) -> list:
            fields = []
            for key,value in self.main.fields.items():
                fields.append(f'{self.main.name}.{key}')
            return fields
        
        def join(self):
            join_fields = self.join_field()
            model_name = ''
            primary_key = ''
            can_join = False

            for key,field in self.main.fields.items():

                if type(field) == type(ForeignKey()):

                    join_fields += field.model().filter().join_field() # type: ignore
                    model_name +=field.model().name # type: ignore
                    primary_key +=field.model().primary_key() or field.model().foreign_key() # type: ignore
                    can_join = True
            
            if not can_join:
                raise NoForeignKey('Can not join with no foreign key')
            
            fields = ''
            for _ in  join_fields:
                fields+=f'{_},'
            filter_query = ''

            for key,value in self.user_input.items():
                
                if key in self.main.fields.keys():
                    filter_query += f'{self.main.name}.{key} LIKE "%{value}%" or '
            
            _query = f'SELECT {fields[:-1]} FROM {self.main.name} LEFT JOIN {model_name} ON {model_name}.{primary_key} = {self.main.name}.{self.main.primary_key() or self.main.foreign_key()} WHERE {filter_query[:-3]}'
            # print(filter_query)
            # print(_query, 'join')
            self.main_query = _query
            
            return execute_query(_query).fetchall() 
    def query(self):
        return self.main_query
        





