Try to register a job with rabbitmq

```bash
docker exec -it debates-debug-cli-1 sh -c "
  curl -X POST http://backend:8000/start-analysis \
  -H 'Content-Type: application/json' \
  -d '{
    \"job_id\": \"2a1e546e-2b34-4283-901a-41d76b90f6e0\",
    \"s3_key\": \"2a1e546e-2b34-4283-901a-41d76b90f6e0/media/minidebates.mp4\",
    \"title\": \"Curl Test Upload\"
  }'
"
```
