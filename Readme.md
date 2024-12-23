# MODEL:
* You inherit from the model to get,
    - get : to get all columns you insert in the args and can also limit
        model().get('column_name', LIMIT=10) limit is optional but the args for the columns is needed
    - migration : to create the model model()
        jsut call model().migrate() to create the database
    * Filter:
    -    model().filter(user = 'google').exact() : get user "where user = 'google'"
    -    model().filter(user = 'google).all()  : get user " WHERE user LIKE '% google %'"
        
    -    model().filter(user = 'google').delete() deletes user " WHERE user = '% google %'"
        
    -    model().filter(user = 'google').join() joins if there's a foriegn key  
# FIELDS:
- Char, IntField, TextField, BooleanField, ForeignKey
