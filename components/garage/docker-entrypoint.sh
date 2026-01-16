#!/bin/bash
set -e

echo "🚀 Starting Garage Server..."
garage server &
GARAGE_PID=$!

echo "⏳ Waiting for Garage to initialize..."
until nc -z localhost 3903; do sleep 1; done

# Give the internal gossip protocol a moment to stabilize
sleep 3

echo "🛠  Configuring Garage..."

if ! garage layout show | grep -q "Capacity"; then
    echo "⚙️  Initializing fresh single-node layout..."

    NODE_ID=$(garage node id -q | cut -d'@' -f1)
    echo "   Targeting Node ID: $NODE_ID"

    # Assign with a retry loop (in case node isn't ready)
    MAX_RETRIES=5
    for i in $(seq 1 $MAX_RETRIES); do
        if garage layout assign -z zone1 -c 500MB "$NODE_ID"; then
            echo "   ✅ Assignment successful."
            break
        else
            echo "   ⚠️ Assignment failed (attempt $i/$MAX_RETRIES). Retrying in 2s..."
            sleep 2
        fi
    done

    garage layout apply --version 1 || echo "⚠️ Layout apply warning (might be already applied)"
    echo "✅ Layout configured."
    sleep 2
fi

garage bucket create debates || true

if [ -n "$S3_ACCESS_KEY" ] && [ -n "$S3_SECRET_KEY" ]; then
    echo "🔑 Importing keys..."
    garage key import --yes "$S3_ACCESS_KEY" "$S3_SECRET_KEY" || echo "⚠️ Key import warning (check if key exists)"

    echo "🏷  Renaming key to 'app-key'..."
    garage key rename "$S3_ACCESS_KEY" app-key || echo "⚠️ Rename warning (alias might exist)"

    echo "🔓 Granting permissions..."
    garage bucket allow debates --key "$S3_ACCESS_KEY" --read --write --owner || true
else
    echo "⚠️  No keys provided in ENV."
fi

python3 /setup_cors.py

echo "✅ Garage Setup Complete."
wait $GARAGE_PID
