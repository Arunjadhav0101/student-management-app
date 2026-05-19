import os
import json
import pymysql

def get_connection():
    """Establish and return a MySQL connection."""
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

def lambda_handler(event, context):
    """
    AWS Lambda Function: Activity Logger via API Gateway / SQS / Direct Invocation
    Connects to RDS MySQL to log events.
    Expected event structure (direct): { "user_id": 1, "action": "LOGIN", "details": "User logged in" }
    """
    connection = None
    try:
        connection = get_connection()
        logs_to_insert = []
        
        # Handle SQS batch events if triggered by SQS
        if 'Records' in event:
            for record in event['Records']:
                body = json.loads(record['body'])
                logs_to_insert.append((
                    body.get('user_id'), 
                    body.get('action'), 
                    body.get('details')
                ))
        else:
            # Direct invocation
            logs_to_insert.append((
                event.get('user_id'), 
                event.get('action'), 
                event.get('details')
            ))
            
        # Insert all logs into the database
        with connection.cursor() as cursor:
            sql = "INSERT INTO activity_logs (user_id, action, details) VALUES (%s, %s, %s)"
            cursor.executemany(sql, logs_to_insert)
            
        # Commit the transaction
        connection.commit()
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Activity logged successfully'})
        }
        
    except Exception as e:
        print(f"Error logging activity: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
        
    finally:
        if connection:
            connection.close()
