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

transaction = []
accounts = ["pibarabot", "pibarabank"]
client = Client()
for witness in client.get_active_witnesses():
    accounts.append(witness)
for account in accounts:
    for obj in account_to_fluree_adresses(client, account):
        transaction.append(obj)

print(json.dumps(transaction, indent=4, sort_keys=True))
