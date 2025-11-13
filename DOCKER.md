# 🐳 Docker Deployment Guide for VSRMS

This guide will help you run the Vehicle Service & Repair Management System (VSRMS) using Docker containers.

## 📋 Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose
- At least 2GB RAM available for containers

## 🚀 Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone and navigate to the project directory**
   ```bash
   git clone <repository-url>
   cd car-service-management-system-main
   ```

2. **Build and start the application**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Open your web browser and go to: http://localhost:5000
   - Admin login: `admin@vsrms.com` / `admin123`

### Option 2: Using Docker Commands

1. **Build the Docker image**
   ```bash
   docker build -t vsrms:latest .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name vsrms-app \
     -p 5000:5000 \
     -v $(pwd)/instance:/app/instance \
     vsrms:latest
   ```

3. **Access the application**
   - Open your web browser and go to: http://localhost:5000

## 🔧 Configuration Options

### Environment Variables

You can customize the application using these environment variables:

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `FLASK_ENV` | Flask environment mode | `production` |
| `SECRET_KEY` | Flask secret key | `your-secret-key-change-this-in-production` |
| `DATABASE_URL` | Database connection string | `sqlite:///vehicle_management.db` |
| `PORT` | Application port | `5000` |

### Custom Configuration Example

```bash
docker run -d \
  --name vsrms-app \
  -p 8080:5000 \
  -e FLASK_ENV=development \
  -e SECRET_KEY=my-custom-secret-key \
  -v $(pwd)/instance:/app/instance \
  vsrms:latest
```

## 💾 Database Persistence

### SQLite (Default)
The application uses SQLite by default, and the database file is stored in the `instance/` directory:

```yaml
# In docker-compose.yml
volumes:
  - ./instance:/app/instance
```

### MySQL (Optional)

To use MySQL instead, uncomment the MySQL service in `docker-compose.yml`:

1. **Uncomment MySQL service and volumes in docker-compose.yml**

2. **Update environment variables**
   ```yaml
   environment:
     - DATABASE_URL=mysql+pymysql://vsrms_user:vsrms_password@vsrms-db:3306/vehicle_management
   ```

3. **Start with dependency**
   ```bash
   docker-compose up --build
   ```

## 🔍 Health Monitoring

The application includes health checks:

```bash
# Check container health
docker ps

# View health check logs
docker logs vsrms-web
```

## 📊 Container Management

### Start/Stop Services
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f vsrms-web
```

### Database Management
```bash
# Initialize database (if needed)
docker-compose exec vsrms-web python init_db.py

# Access database shell (SQLite)
docker-compose exec vsrms-web sqlite3 instance/vehicle_management.db

# Backup database
docker cp vsrms-web:/app/instance/vehicle_management.db ./backup_$(date +%Y%m%d).db
```

## 🛠️ Development Mode

For development with hot reloading:

1. **Create development docker-compose override**
   ```yaml
   # docker-compose.dev.yml
   version: '3.8'
   services:
     vsrms-web:
       environment:
         - FLASK_ENV=development
       volumes:
         - .:/app
       command: ["python", "app.py"]
   ```

2. **Start in development mode**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
   ```

## 🔒 Security Considerations

### Production Deployment
- Change the default `SECRET_KEY`
- Use environment variables for sensitive data
- Enable HTTPS with a reverse proxy (nginx/traefik)
- Update default admin credentials immediately

### Example Production Setup
```yaml
services:
  vsrms-web:
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${FLASK_SECRET_KEY}
    restart: unless-stopped
```

## 🧪 Testing the Deployment

### Health Check Commands
```bash
# Test application health
curl http://localhost:5000/

# Check container status
docker-compose ps

# View application logs
docker-compose logs vsrms-web
```

### Default Admin Account
- **Email:** admin@vsrms.com
- **Password:** admin123
- **⚠️ Change these credentials immediately after first login!**

## 🐛 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs vsrms-web

# Rebuild without cache
docker-compose build --no-cache vsrms-web
```

**Database issues:**
```bash
# Reset database
docker-compose down -v
docker-compose up --build

# Manual database initialization
docker-compose exec vsrms-web python init_db.py
```

**Permission issues:**
```bash
# Fix volume permissions
sudo chown -R $USER:$USER instance/
```

### Performance Optimization

**For better performance:**
- Allocate more memory: `docker update --memory=1g vsrms-web`
- Use production WSGI server (gunicorn) in production
- Enable Docker BuildKit: `DOCKER_BUILDKIT=1 docker build`

## 📈 Scaling

### Horizontal Scaling with Load Balancer
```yaml
# docker-compose.scale.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

  vsrms-web:
    scale: 3
    ports: []
```

Run with: `docker-compose up --scale vsrms-web=3`

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up --build -d

# Clean up old images
docker image prune
```

### Backup Strategy
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker cp vsrms-web:/app/instance ./backups/instance_$DATE
tar -czf backups/vsrms_backup_$DATE.tar.gz backups/instance_$DATE
```

## 🆘 Support

If you encounter issues:
1. Check the application logs: `docker-compose logs -f`
2. Verify container health: `docker-compose ps`
3. Test database connectivity: `docker-compose exec vsrms-web python init_db.py`
4. Review this documentation for configuration options

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask Deployment Documentation](https://flask.palletsprojects.com/en/2.0.x/deploying/)

---
*Built with 💙 for efficient vehicle service management*
