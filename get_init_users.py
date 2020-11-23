#!/usr/bin/python3
import json
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

def account_to_fluree_adresses(client, account):
    client = Client()
    accounts = client.get_accounts([account])
    for record in accounts:
        account=record["name"]
        for keytype in ["owner", "active", "posting"]:
            pubkey = record[keytype]["key_auths"][0][0]
            key_id =  hive_pubkey_to_fluree_address(pubkey)
            obj = dict()
            obj["_id"] = "_auth"
            obj["id"] = key_id
            obj["doc"] = account + ":" + keytype
            if account == "pibarabank" and keytype == "active":
                obj["roles"] = [["_role/name", "advertisingBot"]]
            elif account == "pibarabot" and keytype == "active":
                obj["roles"] = [["_role/name", "advertisingBot"]]
            else:
                if account in ["pibarabot", "pibarabank"]:
                    obj["roles"] = []
                else:
                    obj["roles"] = [["_role/name", "Witness" + keytype]]
            yield obj

def process_account_record(account, record, keytype, role):
    if (keytype in record and 
       "key_auths" in record[keytype] and
       isinstance(record[keytype]["key_auths"], list) and
       record[keytype]["key_auths"] and
       isinstance(record[keytype]["key_auths"][0], list) and
       record[keytype]["key_auths"][0]):
        pubkey = record[keytype]["key_auths"][0][0]
        key_id =  hive_pubkey_to_fluree_address(pubkey)
        yield [key_id, role]

def accounts_to_fluree_adresses(client, faccounts, postrole, activerole, ownerrole):
    accounts = client.get_accounts(faccounts)
    for record in accounts:
        account=record["name"]
        rval = dict()
        rval["account"] = account
        rval["result"] = list()
        if postrole:
            for val in process_account_record(account, record, "posting", postrole):
                rval["result"].append(val)
        if activerole:
            for val in process_account_record(account, record, "active", activerole):
                rval["result"].append(val)
        if ownerrole:
            for val in process_account_record(account, record, "owner", ownerrole):
                rval["result"].append(val)
        yield rval

transaction = []
accounts = ["pibarabot", "pibarabank"]
client = Client()
iblock = client.get_dynamic_global_properties()["last_irreversible_block_num"]
witnesses = client.get_witnesses_by_vote("", 1000)
non_dead_witnesses = set()
for witness in witnesses:
    if witness["votes"] and iblock - witness["last_confirmed_block_num"] < 200000:
        non_dead_witnesses.add(witness["owner"])
for result in accounts_to_fluree_adresses(client, list(non_dead_witnesses), "hive_witness_role", "hive_witness_active_role", "hive_witness_owner_role"):
    print(result)

#for witness in client.get_active_witnesses():
#    accounts.append(witness)
#for account in accounts:
#    for obj in account_to_fluree_adresses(client, account):
#        transaction.append(obj)
#
#print(json.dumps(transaction, indent=4, sort_keys=True))
