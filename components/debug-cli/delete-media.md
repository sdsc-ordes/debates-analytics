docker exec -it debug-cli sh -c "
curl -X DELETE http://backend:8000/admin/1a505488-fa96-45ab-b232-295311482a19 \
-H 'Content-Type: application/json'
"


docker exec -it backend python -c "from app.main import api; [print(r.path) for r in api.routes]"