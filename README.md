# Fintech API

FastAPI-based fintech API project

### Tech Stack
- FastAPI
- Python
- SQLAlchemy

### API Endpoints
**/users**
- /users/register
- /users/login

**/wallet**
- /wallet
- /wallet/add-funds - manually add money to an account (for testing purposes)

**/transactions**
- /transactions/send
- /transactions/history

### Features
- User registration
- User authentication
- Password hashing with bcrypt
- View wallet balance
- Money transfer
- Transactions history

### Project History
- Simulated API Gateway using Kong
- Migrated from monolithic to microservices architecture
- Synced the 3 services using the Saga pattern (each step has a compensating rollback action)

### Possible Improvements
- Security gaps: logout doesn't invalidate tokens, no refresh tokens, no HTTPS
- Lacking centralized logging/monitoring
- Unused Redis cache
- No support for currency conversion
