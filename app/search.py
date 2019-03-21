from flask import current_app

#args passed from model are (cls.__tablename__, instance of model)
def add_to_index(index, model):
    # when the Elasticsearch server isn't configured,
    # the application continues to run without the search capability and without giving any errors.
    if not current_app.elasticsearch:
        return
    payload = {}
    #define a general way to extract all the data you marked as being indexable from a given model
    for field in model.__searchable__:
        #each field is entered as a value | body = {columnName1:data,columnName2:data}
        payload[field] = getattr(model, field)
    #the body is a dictionary containing the data from every field marked as "searchable" in the model
    current_app.elasticsearch.index(index=index, doc_type=index, id=model.id, body=payload)

#args passed from model are (cls.__tablename__, instance of model)
def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    #This function deletes the JSON obj containing the given id
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id)


def query_index(index, query, page, per_page):
    #return this if elasticsearch isn't configured
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index, doc_type=index,
        #fields are individual columns that we added to the payload when indexing a record. For Posts, only 1 field is present
        #multimatch used to query multiple fields. [*] means to look in all fields
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}}, 'from': (page - 1) * per_page, 'size': per_page})
    #list of all the element ids from the search results
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    #returns the ids of all the models that matched the query and a total number of matches you got
    return ids, search['hits']['total']