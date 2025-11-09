#!/bin/sh
# This script is executed by the minio-setup container.

echo 'Waiting for Minio...';
# Use the 'wait-for-it' pattern or simple sleep/retry loop if necessary, 
# but rely on 'depends_on: service_healthy' in compose for simplicity.
sleep 5

# Set the alias for the MinIO instance
# Note: $S3_ACCESS_KEY and $S3_SECRET_KEY are passed directly as ENV vars
/usr/bin/mc alias set myminio http://minio-instance:9000 $S3_ACCESS_KEY $S3_SECRET_KEY;
echo 'Alias set.';

# Create the bucket
/usr/bin/mc mb myminio/$S3_BUCKET_NAME || echo 'Bucket already exists or creation failed.';
echo 'Bucket setup complete.';

exit 0;
