Create marker file on s3


```bash
docker exec -it debates-debug-cli-1 sh -c "
  curl -X POST http://backend:8000/create-marker \
  -H 'Content-Type: application/json' \
  -d '{\"job_id\": \"2a1e546e-2b34-4283-901a-41d76b90f6e0\"}'
"
```