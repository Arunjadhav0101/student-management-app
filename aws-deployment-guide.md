# AWS Deployment Guide

This guide explains how to deploy the Student Management Application onto AWS following enterprise best practices.

## Architecture Overview
- **VPC:** 1 Public Subnet (ALB, Frontend EC2), 2 Private Subnets (Backend EC2, RDS Database).
- **Compute:** EC2 instances managed by an Auto Scaling Group (ASG).
- **Database:** AWS RDS for MySQL (Multi-AZ for high availability).
- **Load Balancing:** Application Load Balancer (ALB) routing HTTP/HTTPS traffic.
- **Serverless:** AWS Lambda for asynchronous logging (integrated with API Gateway or SQS).
- **Storage:** S3 for storing profile pictures (if implemented in future).

## Step-by-Step Deployment

### 1. Networking (VPC Setup)
1. Navigate to VPC Dashboard -> Create VPC.
2. Use the "VPC and more" wizard to create a VPC with public and private subnets, along with a NAT Gateway (for backend internet access) and an Internet Gateway.

### 2. Database (AWS RDS)
1. Go to RDS Dashboard -> Create database.
2. Select **MySQL**.
3. Choose the Free Tier or Production template.
4. Set credentials (e.g., `admin` / `rootpassword`).
5. Place the DB in the **Private Subnet** of your VPC.
6. Make sure the security group allows inbound traffic on port 3306 from your Backend EC2 Security Group.
7. Connect to RDS using an EC2 jump server or MySQL Workbench and run the `schema.sql` script to create tables.

### 3. Compute & Scaling (EC2 & ASG)
1. **Launch Template:** Create a launch template for the Backend API.
   - AMI: Ubuntu 22.04 LTS or Amazon Linux 2023.
   - User Data script to install Node.js, clone repository, run `npm install`, and start server using PM2.
   - Assign a role with CloudWatch access.
2. **Auto Scaling Group:** Create an ASG using the template, targeting the private subnets. Set desired capacity to 2.
3. **Application Load Balancer (ALB):** Create an ALB in the public subnets. Route traffic to the Backend ASG Target Group.

### 4. Frontend Deployment (Options)
- **Option A (S3 + CloudFront):** Host the static `/frontend` files in an S3 bucket and distribute via CloudFront CDN. Update `API_URL` in `app.js` to point to the ALB DNS name.
- **Option B (EC2 with Nginx):** Deploy a separate EC2 instance in the public subnet running Nginx. Copy frontend files to `/usr/share/nginx/html`.

### 5. Serverless Logging (AWS Lambda)
1. Go to Lambda Dashboard -> Create Function.
2. Choose Node.js 18.x.
3. Paste the code from `aws-lambda/activity-logger.js`.
4. Add environment variables for RDS connection (`DB_HOST`, `DB_USER`, etc.).
5. Ensure the Lambda function's Execution Role has VPC access and RDS connect permissions.

### 6. DNS and SSL (Route 53 & ACM)
1. Request a public SSL certificate in AWS Certificate Manager (ACM).
2. Create an Alias record in Route 53 pointing your custom domain (e.g., `api.example.com`) to the ALB.

## CI/CD Pipeline (GitHub Actions or AWS CodePipeline)
To automate this, configure a pipeline to:
1. Build Docker images.
2. Push to Amazon ECR.
3. Trigger an EC2 Auto Scaling instance refresh or ECS service update.

## Backend Deployment Script

The following shell script can be used in your EC2 User Data or executed manually to set up the backend environment, deploy the app, and configure monitoring on the EC2 instance:

```bash
#!/bin/bash

LOG_FILE="/home/ubuntu/backend-setup.log"

echo "==============================" >> $LOG_FILE
echo "SETUP STARTED $(date)" >> $LOG_FILE

# Update packages
apt update -y >> $LOG_FILE 2>&1

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >> $LOG_FILE 2>&1

# Install required packages
apt install -y nodejs git >> $LOG_FILE 2>&1

# Install PM2 globally
npm install -g pm2 >> $LOG_FILE 2>&1

# Switch to ubuntu home
cd /home/ubuntu || exit

# Clone project if not exists
if [ ! -d "student-management-app" ]; then
    git clone https://github.com/Arunjadhav0101/student-management-app.git >> $LOG_FILE 2>&1
fi

# Go to backend directory
cd /home/ubuntu/student-management-app/backend || exit

# Install dependencies
npm install >> $LOG_FILE 2>&1

# Create .env file
cat <<EOF > .env
PORT=3000
DB_HOST=student-db.cwjaqaia2aqp.us-east-1.rds.amazonaws.com
DB_USER=admin
DB_PASSWORD=admin9890
DB_NAME=student-db
EOF

# Give ubuntu ownership
chown -R ubuntu:ubuntu /home/ubuntu/student-management-app

# Start backend using ubuntu user
sudo -u ubuntu pm2 delete backend >> $LOG_FILE 2>&1

sudo -u ubuntu pm2 start server.js --name backend >> $LOG_FILE 2>&1

# Save PM2 process
sudo -u ubuntu pm2 save >> $LOG_FILE 2>&1

# Enable PM2 startup
env PATH=$PATH:/usr/bin pm2 startup systemd -u ubuntu --hp /home/ubuntu >> $LOG_FILE 2>&1

# Save again
sudo -u ubuntu pm2 save >> $LOG_FILE 2>&1

# =========================
# Create monitoring script
# =========================

cat <<'EOF' > /home/ubuntu/monitor-backend.sh
#!/bin/bash

LOG_FILE="/home/ubuntu/backend-monitor.log"

echo "==========================" >> $LOG_FILE
echo "Checking backend $(date)" >> $LOG_FILE

# Check PM2 process
PM2_STATUS=$(sudo -u ubuntu pm2 list | grep backend)

if [ -z "$PM2_STATUS" ]; then
    echo "Backend not running. Restarting..." >> $LOG_FILE

    cd /home/ubuntu/student-management-app/backend || exit

    sudo -u ubuntu pm2 start server.js --name backend >> $LOG_FILE 2>&1

    sudo -u ubuntu pm2 save >> $LOG_FILE 2>&1
fi

# Check port 3000
PORT_STATUS=$(ss -tulnp | grep 3000)

if [ -z "$PORT_STATUS" ]; then
    echo "Port 3000 is down. Restarting..." >> $LOG_FILE

    sudo -u ubuntu pm2 restart backend >> $LOG_FILE 2>&1
else
    echo "Port 3000 active." >> $LOG_FILE
fi
EOF

# Make executable
chmod +x /home/ubuntu/monitor-backend.sh

# Add cron job for ubuntu user
sudo -u ubuntu bash -c '(crontab -l 2>/dev/null; echo "* * * * * /home/ubuntu/monitor-backend.sh") | crontab -'

echo "SETUP COMPLETED $(date)" >> $LOG_FILE
```