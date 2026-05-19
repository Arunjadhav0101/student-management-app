// AWS Lambda Function: Activity Logger via API Gateway / SQS / Direct Invocation
// Connects to RDS MySQL to log events

const mysql = require('mysql2/promise');

exports.handler = async (event) => {
    // Expected event structure: { user_id, action, details }
    
    const dbConfig = {
        host: process.env.DB_HOST,
        user: process.env.DB_USER,
        password: process.env.DB_PASSWORD,
        database: process.env.DB_NAME,
    };
    
    let connection;
    try {
        connection = await mysql.createConnection(dbConfig);
        
        let logsToInsert = [];
        
        // Handle SQS batch events if triggered by SQS
        if (event.Records) {
            for (const record of event.Records) {
                const body = JSON.parse(record.body);
                logsToInsert.push([body.user_id, body.action, body.details]);
            }
        } else {
            // Direct invocation
            logsToInsert.push([event.user_id, event.action, event.details]);
        }
        
        for (const log of logsToInsert) {
            await connection.execute(
                'INSERT INTO activity_logs (user_id, action, details) VALUES (?, ?, ?)',
                log
            );
        }
        
        return {
            statusCode: 200,
            body: JSON.stringify({ message: 'Activity logged successfully' }),
        };
    } catch (error) {
        console.error('Error logging activity:', error);
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message }),
        };
    } finally {
        if (connection) {
            await connection.end();
        }
    }
};