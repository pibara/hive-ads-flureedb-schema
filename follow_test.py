#!/usr/bin/python3
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

def accounts_to_fluree_adresses(client, accounts):
    accounts2 = client.get_accounts(accounts)
    for record in accounts2:
        account=record["name"]
        print(" -", account)
        for keytype in ["owner", "active", "posting"]:
            if (keytype in record and
               "key_auths" in record[keytype] and 
               isinstance(record[keytype]["key_auths"], list) and 
               record[keytype]["key_auths"] and 
               isinstance(record[keytype]["key_auths"][0], list) and 
               record[keytype]["key_auths"][0][0]):
                pubkey = record[keytype]["key_auths"][0][0]
                key_id =  hive_pubkey_to_fluree_address(pubkey)
                print("    -", keytype,":", key_id)

client = Client()
oldblock = client.get_dynamic_global_properties()["last_irreversible_block_num"]
accounts = set()
while True:
    count = 0
    skipcount = 0
    newblock = client.get_dynamic_global_properties()["last_irreversible_block_num"]
    for no in range(oldblock, newblock+1):
        print(no-oldblock+1 ,"/" ,newblock-oldblock+1)
        accounts2 = list()
        block = client.get_block(no)
        for transaction in block["transactions"]:
            for operation in transaction["operations"]:
                opp = operation[0]
                found = False
                for key in ["required_auths",
                            "required_posting_auths",
                            "parent_author",
                            "author",
                            "voter",
                            "from",
                            "to",
                            "owner",
                            "account",
                            "publisher",
                            "creator",
                            "delegator",
                            "delegatee"]:
                    if key in operation[1].keys():
                        val = operation[1][key]
                        if isinstance(val, list):
                            for v in val:
                                if v and isinstance(v,str):
                                    found=True
                                    if v not in accounts:
                                        count += 1
                                        accounts.add(v)
                                        accounts2.append(v)
                                    else:
                                        skipcount += 1
                        else:
                            if val and isinstance(val,str):
                                found=True
                                if val not in accounts:
                                    count += 1
                                    accounts.add(val)
                                    accounts2.append(val)
                                else:
                                    skipcount += 1
        if accounts2:
            accounts_to_fluree_adresses(client, accounts2)
        print(" *", count,"/", count+skipcount, "/", len(accounts))
    time.sleep(1)
    oldblock = newblock + 1
