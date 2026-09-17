def test_health_and_ready(client):
    assert client.get('/health').json()['status'] == 'ok'
    assert client.get('/ready').json()['transactions'] == 6000


def test_transaction_and_missing(client):
    assert client.get('/transactions/TXN_0000002').status_code == 200
    assert client.get('/transactions/TXN_9999999').status_code == 404
    assert client.get('/transactions/nope').status_code == 400


def test_investigation_endpoints(client):
    response = client.post('/investigate', json={'transaction_id': 'TXN_0002500'})
    assert response.status_code == 200
    report = response.json()
    assert client.get('/investigations/' + report['investigation_id']).json() == report
    assert client.get('/investigations/absent').status_code == 404
    assert client.post('/investigate', json={'transaction_id': 'bad'}).status_code == 422


def test_chat_validation(client):
    assert client.post('/chat', json={'question': ''}).status_code == 422
    assert client.post('/chat', json={'question': 'hi', 'session_id': 'bad'}).status_code == 400
    assert client.post('/chat', json={'question': 'hi', 'sql': 'SELECT 1'}).status_code == 422
    response = client.post('/chat', json={'question': 'Investigate TXN_0002500'})
    assert response.status_code == 200
    followup = client.post('/chat', json={'question': 'Show previous transactions',
        'session_id': response.json()['session_id']})
    assert followup.status_code == 200 and followup.json()['transactions']
