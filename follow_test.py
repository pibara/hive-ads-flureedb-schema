#!/usr/bin/python3
import sys
import json
import time
import hashlib
import base58
import bitcoinlib
from lighthive.client import Client

def hive_pubkey_to_fluree_address(ownerpubkey): 
    pubkeyb58 = ownerpubkey[3:]
    pubkey = base58.b58decode(pubkeyb58)[:-4]
    bitcoin_pubkey = bitcoinlib.keys.Key(pubkey)
    bitcoin_address = bitcoin_pubkey.address()
    core = b'\x0f\x02' + base58.b58decode(bitcoin_address)[1:-4]
    h1 = hashlib.sha256()
    h2 = hashlib.sha256()
    h1.update(core)
    h2.update(h1.digest())
    keyid = base58.b58encode(core + h2.digest()[:4]).decode()
    return keyid

def accounts_to_fluree_adresses(client, accounts, update=False):
    accounts2 = client.get_accounts(accounts)
    if update:
        for record in accounts2:
            #FIXME: 
            # * Delete all old _auth nodes
            # * Add updated _auth nodes
            pass
    else:
        for record in accounts2:
            account=record["name"]
            transaction = [
                {
                   "_id": "_user",
                   "username": account,
                   "doc": "Regular HIVE user",
                   "auth": [],
                   "roles": []
                }
            ]
            for keytype in ["owner", "active", "posting"]:
                if (keytype in record and
                   "key_auths" in record[keytype] and 
                   isinstance(record[keytype]["key_auths"], list) and 
                   record[keytype]["key_auths"] and 
                   isinstance(record[keytype]["key_auths"][0], list) and 
                   record[keytype]["key_auths"][0][0]):
                    pubkey = record[keytype]["key_auths"][0][0]
                    key_id =  hive_pubkey_to_fluree_address(pubkey)
                    if keytype == "posting":
                        role = "hive_user_role"
                    else:
                        role = "hive_user_" + keytype + "_role"
                    handle = "_auth$" + key_id
                    operation = dict()
                    operation["_id"] = handle
                    operation["doc"] = keytype + "  auth @" + account
                    if keytype == "posting":
                        transaction[0]["roles"] = [["_role/id", role]]
                    else:
                        operation["roles"] = [["_role/id", role]]
                    transaction[0]["auth"].append(handle)
                    transaction.append(operation)
            transaction.reverse()
            print(json.dumps(transaction, indent=2, sort_keys=True))
            print()


account_reference_keys = [
    "account",
    "account_to_recover",
    "agent",
    "author",
    "contributor",
    "control_account",
    "current_owner",
    "creator",
    "delegatee",
    "delegator",
    "from",
    "from_account",
    "new_account_name",
    "open_owner",
    "owner",
    "parent_author",
    "producer",
    "proxy",
    "publisher",
    "receiver",
    "recovery_account",
    "required_auths",
    "required_posting_auths",
    "to",
    "to_account",
    "voter",
    "witness"
]
account_changing_opps = {
    "account_update": "account",
    "recover_account": "account_to_recover"
}
client = Client()
stats = client.get_dynamic_global_properties()
for key in stats:
    if "block" in key:
        print(key,":",stats[key])
sys.exit(0)
oldblock = client.get_dynamic_global_properties()["last_irreversible_block_num"]
accounts = set()
while True:
    count = 0
    skipcount = 0
    newblock = client.get_dynamic_global_properties()["last_irreversible_block_num"]
    for no in range(oldblock, newblock+1):
        accounts2 = set()
        accounts3 = set()
        block = client.get_block(no)
        for transaction in block["transactions"]:
            for operation in transaction["operations"]:
                opp = operation[0]
                for key in account_reference_keys:
                    if key in operation[1].keys():
                        val = operation[1][key]
                        if isinstance(val, list):
                            for v in val:
                                if v and isinstance(v,str):
                                    if v not in accounts:
                                        count += 1
                                        accounts.add(v)
                                        accounts2.add(v)
                                    else:
                                        skipcount += 1
                        else:
                            if val and isinstance(val,str):
                                if val in accounts and opp in account_changing_opps and account_changing_opps[opp] == key:
                                    accounts3.add(val)
                                if val not in accounts:
                                    count += 1
                                    accounts.add(val)
                                    accounts2.add(val)
                                else:
                                    skipcount += 1
        if accounts2:
            accounts_to_fluree_adresses(client, list(accounts2))
        if accounts3:
            accounts_to_fluree_adresses(client, list(accounts3), update=True)
    time.sleep(1)
    oldblock = newblock + 1
