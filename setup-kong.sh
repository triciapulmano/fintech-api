#!/bin/bash

# Kong API Gateway Configuration for Fintech Microservices
# This script sets up all services, routes, and plugins

KONG_ADMIN="http://localhost:8444"
SECRET_KEY="your-secret-key-change-in-production"

echo "🔧 Configuring Kong API Gateway..."

# ===== USERS SERVICE =====
echo ""
echo "📝 Setting up Users Service..."

# Create upstream for users service
curl -s -X POST $KONG_ADMIN/upstreams \
  --data name=users-service \
  --data algorithm=round-robin > /dev/null

# Add target
curl -s -X POST $KONG_ADMIN/upstreams/users-service/targets \
  --data target=users-service:8001 \
  --data weight=100 > /dev/null

# Create service
curl -s -X POST $KONG_ADMIN/services \
  --data name=users-service \
  --data host=users-service \
  --data port=8001 \
  --data protocol=http > /dev/null

# Create route
curl -s -X POST $KONG_ADMIN/services/users-service/routes \
  --data "paths[]=/users" \
  --data name=users-route \
  --data strip_path=false > /dev/null

# Enable rate limiting on users service
curl -s -X POST $KONG_ADMIN/services/users-service/plugins \
  --data name=rate-limiting \
  --data config.minute=1000 \
  --data config.hour=10000 > /dev/null

# Enable CORS
curl -s -X POST $KONG_ADMIN/services/users-service/plugins \
  --data name=cors \
  --data config.origins=* \
  --data config.methods=GET,POST,PUT,DELETE,PATCH \
  --data config.allow_headers=Content-Type,Authorization > /dev/null

echo "✓ Users Service configured"

# ===== WALLET SERVICE =====
echo ""
echo "💰 Setting up Wallet Service..."

curl -s -X POST $KONG_ADMIN/upstreams \
  --data name=wallet-service \
  --data algorithm=round-robin > /dev/null

curl -s -X POST $KONG_ADMIN/upstreams/wallet-service/targets \
  --data target=wallet-service:8002 \
  --data weight=100 > /dev/null

curl -s -X POST $KONG_ADMIN/services \
  --data name=wallet-service \
  --data host=wallet-service \
  --data port=8002 \
  --data protocol=http > /dev/null

curl -s -X POST $KONG_ADMIN/services/wallet-service/routes \
  --data "paths[]=/wallet" \
  --data name=wallet-route \
  --data strip_path=false > /dev/null

# Key auth for wallet service
curl -s -X POST $KONG_ADMIN/services/wallet-service/plugins \
  --data name=key-auth \
  --data config.key_names=X-API-Key > /dev/null 2>&1 || true

# Rate limiting
curl -s -X POST $KONG_ADMIN/services/wallet-service/plugins \
  --data name=rate-limiting \
  --data config.minute=500 \
  --data config.hour=5000 > /dev/null

# CORS
curl -s -X POST $KONG_ADMIN/services/wallet-service/plugins \
  --data name=cors \
  --data config.origins=* \
  --data config.methods=GET,POST,PUT,DELETE,PATCH \
  --data config.allow_headers=Content-Type,Authorization > /dev/null

echo "✓ Wallet Service configured"

# ===== TRANSACTIONS SERVICE =====
echo ""
echo "💸 Setting up Transactions Service..."

curl -s -X POST $KONG_ADMIN/upstreams \
  --data name=transactions-service \
  --data algorithm=round-robin > /dev/null

curl -s -X POST $KONG_ADMIN/upstreams/transactions-service/targets \
  --data target=transactions-service:8003 \
  --data weight=100 > /dev/null

curl -s -X POST $KONG_ADMIN/services \
  --data name=transactions-service \
  --data host=transactions-service \
  --data port=8003 \
  --data protocol=http > /dev/null

curl -s -X POST $KONG_ADMIN/services/transactions-service/routes \
  --data "paths[]=/transactions" \
  --data name=transactions-route \
  --data strip_path=false > /dev/null

# Rate limiting on transactions
curl -s -X POST $KONG_ADMIN/services/transactions-service/plugins \
  --data name=rate-limiting \
  --data config.minute=100 \
  --data config.hour=1000 > /dev/null

# CORS
curl -s -X POST $KONG_ADMIN/services/transactions-service/plugins \
  --data name=cors \
  --data config.origins=* \
  --data config.methods=GET,POST,PUT,DELETE,PATCH \
  --data config.allow_headers=Content-Type,Authorization > /dev/null

echo "✓ Transactions Service configured"

# ===== CREATE TEST CONSUMER =====
echo ""
echo "👤 Creating test consumer..."

curl -s -X POST $KONG_ADMIN/consumers \
  --data username=test-client \
  --data custom_id=test_client_001 > /dev/null

# Create API key
curl -s -X POST $KONG_ADMIN/consumers/test-client/key-auth \
  --data key=test-api-key-12345 > /dev/null

echo "✓ Test consumer created"

echo ""
echo "✅ Kong configuration complete!"
echo ""
echo "Test endpoints:"
echo "  Register: curl -X POST http://localhost:8000/users/register -H 'Content-Type: application/json' -d '{\"phone_number\":\"+1234567890\",\"username\":\"john\",\"password\":\"SecurePass123!\"}'"
echo "  Login: curl -X POST http://localhost:8000/users/login -H 'Content-Type: application/json' -d '{\"phone_number\":\"+1234567890\",\"password\":\"SecurePass123!\"}'"
echo "  Get Wallet: curl -X GET http://localhost:8000/wallet -H 'Authorization: Bearer <token>'"
echo "  Add Funds: curl -X POST http://localhost:8000/wallet/add-funds -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' -d '{\"amount\":100}'"
echo "  Transaction History: curl -X GET http://localhost:8000/transactions/history -H 'Authorization: Bearer <token>'"