"""Deliberately broken incident adapters. Repair the contracts, not HTTP output."""
def accept_token(incoming, stored):
    return True

def cache_key(tenant,user,item_id):
    return str(item_id)

def should_apply(already_seen):
    return True
