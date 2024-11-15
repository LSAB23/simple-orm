from functools import lru_cache


class Field:
    def __init__(self,
        name :str=None,
        max_length :int= None,
        null :bool= True,
        default :str|int= None,
        primary_key :bool= False,
        model :object= None
        ):
        self.name :str|None= name
        self.max_length :int= max_length or 256
        self.null :bool= null
        self.default :str|int|None= default
        self.is_primary :bool= primary_key
        self.model :object= model

    @lru_cache
    def new_table_query(self) -> tuple:
        fields = {
            'Char': 'VARCHAR',
            'IntField':'INTEGER',
            'TextField': 'TEXT',
            'BooleanField': 'BOOLEAN'
        }
        field = self.__class__.__name__
        if field == 'BooleanField':
            self.max_length = 1
        table_name = str(f'"{self.name}"').replace(' ','_')
        if field == 'IntField':
            query = f' {fields[field]},'
        else:
            query = f' {fields[field]}({self.max_length}),'
        
        if not self.null:
            query = query.replace(',','')
            query+= ' NOT NULL,'
        if self.is_primary:
            
            query = query.replace(',','')
            if field == 'IntField':
                query+= ' PRIMARY KEY AUTOINCREMENT,'
            

        return table_name, query
    def check(self, value=None) -> bool:
        return False
    
    def _is_primary_key(self) -> bool:
        if self.__class__.__name__ == 'IntField':
            return self.is_primary
        return False
    
    def _is_foreign_key(self) -> bool:
        if self.__class__.__name__ == 'ForeignKey':
            return True
        return False
    

class Char(Field):
    '''
        name of the charfield default is None

        max_lenght charfield default is 256

        null default is True

        default for  None
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)


    def check(self, value=None) -> bool:
        value = str(value)
        return self.max_length >= len(value)

class IntField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def check(self, value=None) -> bool:
        value = value
        end = True
        if not self.is_primary:
            if isinstance(value ,int):
                if self.max_length <= int(value): # type: ignore
                    return False
        return end
    


class TextField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
    def check(self, value=None) -> bool:    
        value = str(value)
        return self.max_length >= len(value)


class BooleanField(Field):
    def __init__(self, *args,**kwargs):
        super().__init__(*args, **kwargs)

    def check(self, value=None) -> bool:
        if isinstance(value, bool):
            return True
        return False

    
class ForeignKey(Field):
    def __init__(self, *args ,**kwargs):
        super().__init__(*args ,**kwargs)
        self.null = False

    def new_table_query(self) -> tuple:
        model_name= self.model().__class__.__name__ # type: ignore

        name,table_name = IntField(name=self.name).new_table_query()
        table_name = name+table_name
        query = f' FOREIGN KEY({self.name}) REFERENCES {model_name}("{self.model().primary_key()}"),' # type: ignore


        return table_name, query


    def check(self, value=None) -> bool:
        return True