from textwrap import dedent
from flask import Flask
from uuid import uuid4
from blockchain import Blockchain
from flask import jsonify, request
import os
import sys
# creates our node (one node out of many which can connect)
app = Flask(__name__)

# creates a random name, a node identifier.
if len(sys.argv[1]) == 32:
    node_identifier = sys.argv[1]
else:
    print("Error: Unknown node identifier")
    input()
    sys.exit()

# creates an instance of the blockchain
blockchain = Blockchain()

# @app.route() creates access points to the blockchain instance as an api, allowing users to interact with the blockchain.
# here we define a few access points

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transactions(sender = "0", recipient = node_identifier, amount = 1)
    
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New block created',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': proof,
        'previous_hash': previous_hash,
    }
    
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    balance = blockchain.retrieve_balance(values['sender'])
    if balance < values['amount']:
        response = {
            'message': 'Error: Insufficient balance'
        }
        
        return response, 400
        
    index = blockchain.new_transactions(values['sender'], values['recipient'], values['amount'])

    response = {
        'message': f'Transaction will be added to block {index}'
    }

    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/nodes/balance', methods=['POST'])
def retrieve_balance():
    values = request.get_json()

    addr = values.get('address')
    if addr is None:
        return "Error: Missing Address", 400
    balance = blockchain.retrieve_balance(addr)
    response = {
        'balance': balance,
    }
    
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node, node_identifier)
    
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.node_identifiers),
    }
    
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Current chain on node has been replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Current chain is authoritative',
            'chain': blockchain.chain
        }
    
    return jsonify(response), 200

# runs the server on port 8080
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False,  port=os.environ.get('PORT', 8080))
