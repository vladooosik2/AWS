import boto3  

class DataBase:
    def __init__(self, table_name):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def __str__(self):
        return str(self.table)