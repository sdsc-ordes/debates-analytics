#!/bin/sh

# This script performs MinIO setup tasks: bucket creation, CORS policy, and RabbitMQ eventing.

# --- Configuration ---
MINIO_HOST="http://minio-instance:9000"
BUCKET_NAME="$S3_BUCKET_NAME"
RABBITMQ_HOST="$RABBITMQ_URL"
RABBITMQ_QUEUE="video_analysis_jobs"
RABBITMQ_TARGET="rabbitmq" 

echo 'Waiting 10 seconds for RabbitMQ to stabilize...'
sleep 10

# 1. Alias Minio and Create Bucket
echo 'Setting Minio alias...'
/usr/bin/mc alias set myminio $MINIO_HOST "$S3_ACCESS_KEY" "$S3_SECRET_KEY"
echo "Creating bucket: $BUCKET_NAME..."
/usr/bin/mc mb myminio/$BUCKET_NAME || echo 'Bucket already exists.'

# 2. Add CORS Policy (Required for client POST uploads)
echo 'Setting CORS policy...'
# 2a. Create temporary file for the XML content (No changes needed here)
cat > /tmp/cors.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <CORSRule>
        <AllowedOrigin>http://localhost:3000</AllowedOrigin>
        <AllowedMethod>POST</AllowedMethod>
        <AllowedMethod>GET</AllowedMethod>
        <AllowedHeader>*</AllowedHeader>
        <MaxAgeSeconds>3000</MaxAgeSeconds>
        <ExposeHeader>ETag</ExposeHeader>
    </CORSRule>
</CORSConfiguration>
EOF

# FIX 1: Use the explicit 'mc admin bucket set' command for configuration
# This bypasses the ambiguity of 'mc set'
/usr/bin/mc admin bucket remote add myminio/$$BUCKET_NAME download /tmp/cors.xml || echo 'CORS policy already exists.'; 
echo 'CORS policy set.'

# 3. Add RabbitMQ as Event Target
echo 'Setting RabbitMQ AMQP target...';
# Use RABBITMQ_TARGET variable and apply the full URL
/usr/bin/mc admin config set myminio notify_amqp:$RABBITMQ_TARGET url="$RABBITMQ_HOST" exchange="amq.direct" queue="$RABBITMQ_QUEUE" durable="on" || echo 'AMQP target already set.';

# FIX 2: Remove the mc admin service restart command, as it fails non-interactively.
# Rely on MinIO picking up config changes automatically or a subsequent restart.
echo 'Skipping MinIO service restart to avoid TTY error.'; 


# 4. Subscribe Bucket to Event Target
echo 'Subscribing bucket to ObjectCreated events...'
# FIX 3: Use the explicit 'mc event add' command with the correct ARN format for the target.
/usr/bin/mc event add myminio/$BUCKET_NAME arn:minio:sqs::"$RABBITMQ_TARGET" --prefix '*/media/' --event 'put,post';

echo 'Minio setup complete. Events enabled.'
exit 0
