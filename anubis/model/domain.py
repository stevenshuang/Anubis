from pymongo import errors

from anubis import db
from anubis import error
from anubis.model import builtin
from anubis.util import argmethod
from anubis.util import validator

PROJECTION_PUBLIC = {'uid': 1}


@argmethod.wrap
async def add(domain_id: str, owner_uid: int,
              roles=builtin.DOMAIN_SYSTEM['roles'],
              name: str=None, gravatar: str=None):
    validator.check_domain_id(domain_id)
    validator.check_name(name)
    for domain in builtin.DOMAINS:
        if domain['_id'] == domain_id:
            raise error.DomainAlreadyExistError(domain_id)
    coll = db.Collection('domain')
    try:
        return await coll.insert({
            '_id': domain_id,
            'owner_uid': owner_uid,
            'roles': roles,
            'name': name,
            'gravatar': gravatar
        })
    except errors.DuplicateKeyError:
        raise error.DomainAlreadyExistError(domain_id) from None


@argmethod.wrap
async def get(domain_id: str, fields=None):
    for domain in builtin.DOMAINS:
        if domain['_id'] == domain_id:
            return domain
    coll = db.Collection('domain')
    return await coll.find_one(domain_id, fields)


def get_multi(*, fields=None, **kwargs):
    coll = db.Collection('domain')
    return coll.find(kwargs, fields)


@argmethod.wrap
async def edit(domain_id: str, **kwargs):
    for domain in builtin.DOMAINS:
        if domain['_id'] == domain_id:
            return None
    coll = db.Collection('domain')
    if 'owner_uid' in kwargs:
        del kwargs['owner_uid']
    if 'name' in kwargs:
        validator.check_name(kwargs['name'])
    # TODO: check kwargs.
    return await coll.find_and_modify(query={'_id': domain_id},
                                      update={'$set': {**kwargs}},
                                      new=True)


async def unset(domain_id, fields):
    # TODO: check fields.
    coll = db.Collection('domain')
    return await coll.find_and_modify(query={'_id': domain_id},
                                      update={'$unset': dict((f, '') for f in set(fields))},
                                      new=True)


@argmethod.wrap
async def set_role(domain_id: str, role: str, perm: int):
    validator.check_role(role)
    for domain in builtin.DOMAINS:
        if domain['_id'] == domain_id:
            return domain
    coll = db.Collection('domain')
    return await coll.find_and_modify(query={'_id': domain_id},
                                      update={'$set': {'roles.{0}'.format(role): perm}},
                                      new=True)


@argmethod.wrap
async def delete_role(domain_id: str, role: str):
    validator.check_role(role)
    for domain in builtin.DOMAINS:
        if domain['_id'] == domain_id:
            return domain
    user_coll = db.Collection('domain.user')
    await user_coll.update({'domain_id': domain_id, 'role': role},
                           {'$unset': {'role': ''}}, multi=True)
    coll = db.Collection('domain')
    return await coll.find_and_modify(query={'_id': domain_id},
                                      update={'$unset': {'roles.{0}'.format(role): ''}},
                                      new=True)


@argmethod.wrap
async def transfer(domain_id: str, old_owner_uid: int, new_owner_uid: int):
    for domain in builtin.DOMAINS:
        if domain['_id'] == domain_id:
            return None
    coll = db.Collection('domain')
    return await coll.find_and_modify(query={'_id': domain_id, 'owner_uid': old_owner_uid},
                                      update={'$set': {'owner_uid': new_owner_uid}},
                                      new=True)


@argmethod.wrap
async def get_user(domain_id: str, uid: int, fields=None):
    coll = db.Collection('domain.user')
    return await coll.find_one({'domain_id': domain_id, 'uid': uid}, fields)


async def set_user(domain_id, uid, **kwargs):
    coll = db.Collection('domain.user')
    return await coll.find_and_modify(query={'domain_id': domain_id, 'uid': uid},
                                      update={'$set': kwargs},
                                      upsert=True, new=True)


async def unset_user(domain_id, uid, fields):
    coll = db.Collection('domain.user')
    return await coll.find_and_modify(query={'domain_id': domain_id, 'uid': uid},
                                      update={'$unset': dict((f, '') for f in set(fields))},
                                      upsert=True, new=True)


@argmethod.wrap
async def set_user_role(domain_id: str, uid: int, role: str):
    validator.check_role(role)
    return await set_user(domain_id, uid, role=role)


@argmethod.wrap
async def unset_user_role(domain_id: str, uid: int):
    return await unset_user(domain_id, uid, ['role'])


@argmethod.wrap
async def inc_user(domain_id, uid, **kwargs):
    coll = db.Collection('domain.user')
    return await coll.find_and_modify(query={'domain_id': domain_id, 'uid': uid},
                                      update={'$inc': kwargs},
                                      upsert=True, new=True)


def get_multi_user(*, fields=None, **kwargs):
    coll = db.Collection('domain.user')
    return coll.find(kwargs, fields)


async def get_dict_user_by_uid(domain_id, s_uid, *, fields=None):
    result = dict()
    async for dudoc in get_multi_user(domain_id=domain_id, uid={'$in': list(set(s_uid))}, fields=fields):
            result[dudoc['uid']] = dudoc
    return result


async def get_dict_user_by_domain_id(uid, *, fields=None):
    result = dict()
    async for dudoc in get_multi_user(uid=uid, fields=fields):
        result[dudoc['domain_id']] = dudoc
    return result


@argmethod.wrap
async def ensure_indexes():
    coll = db.Collection('domain')
    await coll.ensure_index('owner_uid')
    user_coll = db.Collection('domain.user')
    await user_coll.ensure_index('uid')
    await user_coll.ensure_index([('domain_id', 1),
                                  ('uid', 1)], unique=True)
    await user_coll.ensure_index([('domain_id', 1),
                                  ('role', 1)], sparse=True)


if __name__ == '__main__':
    argmethod.invoke_by_args()
