## List media

4.  **Execute the API call from the CLI container:** (Replace `[CONTAINER_ID]`
    with the ID from the previous step.)

```bash
docker exec -it debates-debug-cli-1 sh -c "
curl -s -X GET http://backend:8000/list \
-H 'Content-Type: application/json'
"
```
