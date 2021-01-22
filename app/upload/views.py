from rest_framework.decorators import api_view
from rest_framework.response import Response
import json

import pydgraph

client_stub = pydgraph.DgraphClientStub \
    .from_slash_endpoint(
        "https://ee.eu-central-1.aws.cloud.dgraph.io/graphql",
        "uns410v4fVKceKl2SLEifExFXtFuDbwclhJHF3H5e/8=")
client = pydgraph.DgraphClient(client_stub)


# Query for data.
def query_1(client):
    query = """
    {
     queryTeam(func: type(Team))  {
     Team.name
     Team.department
     }
     }"""
    txn = client.txn()
    try:
        res = txn.query(query)
        ppl = json.loads(res.json)
        print(ppl)
    finally:
        txn.discard()
    return ppl


@api_view(['GET'])
def Message(request):
    '''
    returns the message for demo
    '''
    message = request.query_params.get('message', 'creating_api in')
    d1 = {'message': message}
    return Response(d1)


@api_view(['GET'])
def People(request):
    '''
    returns the People and there friends
    '''

    ppl = query_1(client)
    return Response(ppl)
