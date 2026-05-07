# PCARA Port Configuration

To avoid conflicts with other projects, PCARA uses non-standard ports:

## Service Ports

| Service     | External Port | Internal Port | Standard Port |
|-------------|---------------|---------------|---------------|
| Frontend    | 3001          | 3000          | 3000          |
| API Gateway | 8081          | 8080          | 8080          |
| PostgreSQL  | 5433          | 5432          | 5432          |
| Redis       | 6380          | 6379          | 6379          |
| ChromaDB    | 8001          | 8000          | 8000          |

## Quick Access URLs

- **Frontend Application**: http://localhost:3001
- **API Documentation**: http://localhost:8081/docs
- **API Health Check**: http://localhost:8081/health
- **ChromaDB**: http://localhost:8001

## Database Connection

For external database clients:
```
Host: localhost
Port: 5433
Database: pcara_dev
Username: pcara_user
Password: pcara_dev_password
```

## Redis Connection

For external Redis clients:
```
Host: localhost
Port: 6380
```

This configuration allows PCARA to run alongside other development projects without port conflicts.