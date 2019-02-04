from cloud.aws import *


# Define the input output format of the function.
# This information is used when creating the *SDK*.
info = {
    'input_format': {
        'session_id': 'str',
        'item_id': 'str',
        'item': 'map',
        'read_permissions': 'list',
        'write_permissions': 'list',
    },
    'output_format': {
        'success': 'bool',
    }
}


def do(data, boto3):
    response = {}
    recipe = data['recipe']
    params = data['params']
    app_id = data['app_id']
    user = data['user']

    user_group = user.get('group', None)

    item_id = params.get('item_id', None)
    new_item = params.get('item', {})
    read_permissions = params.get('read_permissions', [])
    write_permissions = params.get('write_permissions', [])

    new_item['read_permissions'] = read_permissions
    new_item['write_permissions'] = write_permissions

    table_name = '{}-{}'.format(recipe['recipe_type'], app_id)

    dynamo = DynamoDB(boto3)

    result = dynamo.get_item(table_name, item_id)
    item = result.get('Item', {})

    write_permissions = item.get('write_permissions', [])
    if 'all' in write_permissions or user_group in write_permissions:
        dynamo.update_item(table_name, item_id, new_item)
        response['success'] = True
    else:
        response['success'] = False
        response['message'] = 'permission denied'
    return response
