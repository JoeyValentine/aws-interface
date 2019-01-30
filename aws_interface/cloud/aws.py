import json
import uuid
import time
from boto3.dynamodb.conditions import Key


class APIGateway:
    def __init__(self, boto3_session):
        self.client = boto3_session.client('apigateway')

    def connect_with_lambda(self, api_name):
        apis = self.get_rest_apis().get('items', [])
        rest_api_id = None
        for api in apis:
            if api.get('name') == api_name:
                rest_api_id = api.get('id', None)
                break

        return

    def put_method(self, rest_api_id, resource_id, method_type='POST', auth_type='AWS_IAM'):
        response = self.client.put_method(
            restApiId=rest_api_id,
            resourceId=resource_id,
            httpMethod=method_type,
            authorizationType=auth_type,
            apiKeyRequired=False,
        )
        return response

    def get_rest_apis(self):
        response = self.client.get_rest_apis(
            limit=100
        )
        return response

    def create_rest_api(self, api_name):
        response = self.client.create_rest_api(
            name=api_name,
            minimumCompressionSize=128,
            apiKeySource='HEADER',
            endpointConfiguration={
                'types': [
                    'EDGE'
                ]
            }
        )
        return response

    def create_resource(self, rest_api_id, parent_id, path_part):
        response = self.client.create_resource(
            restApiId=rest_api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return response

    def get_resources(self, rest_api_id):
        response = self.client.get_resources(
            restApiId=rest_api_id,
            limit=100,
        )
        return response

    def delete_rest_api(self, rest_api_id):
        return self.client.delete_rest_api(
            restApiId=rest_api_id
        )


class DynamoDB:
    def __init__(self, boto3_session):
        self.client = boto3_session.client('dynamodb')
        self.resource = boto3_session.resource('dynamodb')

    def init_table(self, table_name):
        self.create_table(table_name)
        self.update_table(table_name, indexes=[{
            'hash_key': 'partition',
            'hash_key_type': 'S',
            'sort_key': 'creationDate',
            'sort_key_type': 'N'
        }])

    def create_table(self, table_name):
        try:
            response = self.client.create_table(
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    }
                ],
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                },
                StreamSpecification={
                    'StreamEnabled': True,
                    'StreamViewType': 'KEYS_ONLY'
                }
            )
            return response
        except:
            return None

    def update_table(self, table_name, indexes):
        attr_updates = []
        index_updates = []
        for index in indexes:
            hash_key = index['hash_key']
            hash_key_type = index['hash_key_type']
            sort_key = index.get('sort_key', None)
            sort_key_type = index.get('sort_key_type', None)
            key_schema = [
                {
                    'AttributeName': hash_key,
                    'KeyType': 'HASH'
                }
            ]
            if sort_key:
                index_name = hash_key + '-' + sort_key
                key_schema.append({
                    'AttributeName': sort_key,
                    'KeyType': 'RANGE'
                })
            else:
                index_name = hash_key
            index_create = {
                    'Create': {
                        'IndexName': index_name,
                        'KeySchema': key_schema,
                        'Projection': {
                            'ProjectionType': 'ALL'
                        },
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 1,
                            'WriteCapacityUnits': 1
                        }
                    }
                }
            hash_key_update = {
                'AttributeName': hash_key,
                'AttributeType': hash_key_type
            }
            index_updates.append(index_create)
            attr_updates.append(hash_key_update)
            if sort_key:
                sort_key_update = {
                    'AttributeName': sort_key,
                    'AttributeType': sort_key_type
                }
                attr_updates.append(sort_key_update)
        try:
            response = self.client.update_table(
                AttributeDefinitions=attr_updates,
                TableName=table_name,
                GlobalSecondaryIndexUpdates=index_updates
            )
        except:
            return None
        return response

    def delete_item(self, table_name, partition, item_id):
        response = self.client.delete_item(
            TableName=table_name,
            Key={
                'id': {
                    'S': item_id
                }
            }
        )
        self._add_item_count(table_name, '{}-count'.format(partition), value_to_add=-1)
        return response

    def get_item(self, table_name, item_id):
        table = self.resource.Table(table_name)
        item = table.get_item(Key={
            'id': item_id
        })
        return item

    def get_items(self, table_name, partition, exclusive_start_key=None, limit=100):
        index_name = 'partition-creationDate'
        table = self.resource.Table(table_name)
        if exclusive_start_key:
            response = table.query(
                IndexName=index_name,
                Limit=limit,
                ConsistentRead=False,
                ExclusiveStartKey=exclusive_start_key,
                KeyConditionExpression=Key('partition').eq(partition)
            )
        else:
            response = table.query(
                IndexName=index_name,
                Limit=limit,
                ConsistentRead=False,
                KeyConditionExpression=Key('partition').eq(partition),
            )
        return response

    def put_item(self, table_name, partition, item, item_id=None, creation_date=None):
        if not item_id:
            item_id = str(uuid.uuid4())
        if not creation_date:
            creation_date = int(time.time())
        table = self.resource.Table(table_name)
        item['id'] = item_id
        item['creationDate'] = creation_date
        item['partition'] = partition
        response = table.put_item(
            TableName=table_name,
            Item=item,
        )
        self._add_item_count(table_name, '{}-count'.format(partition))
        return response

    def _put_item_count(self, table_name, count_id, value):
        response = self.put_item(table_name, 'meta_info', {'count': value}, item_id=count_id)
        return response

    def _add_item_count(self, table_name, count_id, value_to_add=1):
        response = self.client.update_item(
            ExpressionAttributeNames={
                '#A': 'count',
            },
            ExpressionAttributeValues={
                ':v': {
                    'N': str(value_to_add),
                }
            },
            Key={
                'id': {
                    'S': count_id,
                }
            },
            ReturnValues='ALL_NEW',
            TableName=table_name,
            UpdateExpression='ADD #A :v',
        )
        return response

    def get_item_count(self, table_name, count_id):
        response = self.get_item(table_name, count_id)
        return response


class Lambda:
    def __init__(self, boto3_session):
        self.client = boto3_session.client('lambda')

    def create_function(self, name, description, runtime, role_arn, handler, zip_file):
        response = self.client.create_function(
            FunctionName=name,
            Runtime=runtime,
            Role=role_arn,
            Handler=handler,
            Code={
                'ZipFile': zip_file
            },
            Description=description,
            Timeout=128,
            MemorySize=128,
            Publish=True,
            TracingConfig={
                'Mode': 'Active'
            },
        )
        return response

    def update_function_code(self, name, zip_file):
        response = self.client.update_function_code(
            FunctionName=name,
            ZipFile=zip_file,
            Publish=True
        )
        return response


class IAM:
    def __init__(self, boto3_session):
        self.client = boto3_session.client('iam')
        self.resource = boto3_session.resource('iam')

    def create_role_and_attach_policies(self, role_name):
        policy_arns = [
            'arn:aws:iam::aws:policy/AWSLambdaExecute',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
            'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            'arn:aws:iam::aws:policy/AWSXrayFullAccess',
        ]
        self.create_role(role_name)
        self.attach_policies(role_name, policy_arns)
        return self.get_role_arn(role_name)

    def get_role_arn(self, role_name):
        role = self.resource.Role(role_name)
        role_arn = role.arn
        return role_arn

    def create_role(self, role_name):
        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        assume_role_policy_document = json.dumps(assume_role_policy_document)
        try:
            response = self.client.create_role(
                Path='/',
                RoleName=role_name,
                AssumeRolePolicyDocument=assume_role_policy_document,
            )
        except:
            print('Already have a role', role_name)
            return None
        return response

    def attach_policies(self, role_name, policy_arns):
        for policy_arn in policy_arns:
            self.attach_policy(role_name, policy_arn)

    def attach_policy(self, role_name, policy_arn):
        try:
            response = self.client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        except:
            print('Fail to attach policy')
            return None
        return response


class CostExplorer:
    def __init__(self, boto3_session):
        self.client = boto3_session.client('ce', 'us-east-1')

    def get_cost_and_usage(self, start, end):
        response = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity='MONTHLY',
            Metrics=['AmortizedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                },
            ],
        )
        return response

    def get_cost(self, start, end):
        response = self.client.get_cost_and_usage(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity='MONTHLY',
            Metrics=['BLENDED_COST']
        )
        return response
