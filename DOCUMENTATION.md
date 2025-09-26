# 📝 Naebak Gateway - Documentation

**Date:** September 26, 2025  
**Version:** 1.0.0  

---

## 🎯 **1. Overview**

The `naebak-gateway` service is the central API Gateway for the Naebak platform. It acts as a single entry point for all client requests and routes them to the appropriate microservices. The gateway is responsible for handling cross-cutting concerns such as authentication, rate limiting, load balancing, and logging.

### **1.1 Key Features**

- **Service Routing:** Dynamically routes requests to backend services based on path prefixes.
- **Load Balancing:** Distributes incoming requests across multiple instances of a service using a round-robin strategy.
- **Authentication:** Secures endpoints using JWT-based authentication and authorization.
- **Rate Limiting:** Protects services from excessive traffic with configurable rate limits.
- **CORS:** Handles Cross-Origin Resource Sharing (CORS) for web applications.
- **Health Checks:** Provides a health check endpoint for monitoring.

---

## 🛠️ **2. Setup and Installation**

### **2.1 Prerequisites**

- Python 3.11+
- pip
- Docker (optional, for containerized deployment)

### **2.2 Installation**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/naebak/naebak-gateway.git
   cd naebak-gateway
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory and add the necessary configurations. See the `config.py` file for a list of all available options.

4. **Run the application:**
   ```bash
   python gateway.py
   ```

---

## 🗺️ **3. Routing Rules**

The gateway uses a path-based routing system to direct requests to the appropriate microservices. The routing rules are defined in the `SERVICE_ROUTES` dictionary in `gateway.py`.

| Path Prefix        | Service Name                  | Authentication Required | Admin Only |
|--------------------|-------------------------------|-------------------------|------------|
| `/api/auth/`       | `naebak-auth-service`         | No                      | No         |
| `/api/admin/`      | `naebak-admin-service`        | Yes                     | Yes        |
| `/api/complaints/` | `naebak-complaints-service`   | Yes                     | No         |
| `/api/messages/`   | `naebak-messaging-service`    | Yes                     | No         |
| `/api/ratings/`    | `naebak-ratings-service`      | Yes                     | No         |
| `/api/visitors/`   | `naebak-visitor-counter-service`| No                      | No         |
| `/api/news/`       | `naebak-news-service`         | No                      | No         |
| `/api/notifications/`| `naebak-notifications-service`| Yes                     | No         |
| `/api/banners/`    | `naebak-banner-service`       | No                      | No         |
| `/api/content/`    | `naebak-content-service`      | No                      | No         |
| `/api/statistics/` | `naebak-statistics-service`   | No                      | No         |
| `/api/themes/`     | `naebak-theme-service`        | Yes                     | No         |

---

## 🔐 **4. Authentication**

The gateway uses JWT (JSON Web Tokens) for authentication. Protected routes require a valid JWT to be included in the `Authorization` header as a Bearer token.

- **Header Format:** `Authorization: Bearer <your-jwt-token>`

### **4.1 Authentication Middleware**

The `check_authentication` function in `gateway.py` is responsible for:

1. Checking if a route requires authentication.
2. Validating the JWT token from the `Authorization` header.
3. Verifying the token's signature and expiration.
4. Checking for admin privileges if the route requires it.

---

## ⚖️ **5. Rate Limiting**

Rate limiting is implemented using the `Flask-Limiter` library. The limits are defined in `config.py` and can be configured using environment variables.

- **Default Limit:** `100` requests per hour per IP address.
- **Authenticated User Limit:** `200` requests per hour per IP address.
- **Public Endpoint Limit:** `50` requests per hour per IP address.

---

## 🚀 **6. Deployment**

The gateway can be deployed as a standalone Python application or as a Docker container.

### **6.1 Standalone Deployment**

```bash
# Set environment variables
export FLASK_APP=gateway.py
export FLASK_ENV=production

# Run with a production-ready WSGI server like Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8013 gateway:app
```

### **6.2 Docker Deployment**

A `Dockerfile` is provided for building a container image.

```bash
# Build the Docker image
docker build -t naebak-gateway .

# Run the Docker container
docker run -d -p 8013:8013 --name naebak-gateway naebak-gateway
```

---

## 📊 **7. Monitoring**

The gateway provides a `/health` endpoint for monitoring its status.

- **Endpoint:** `/health`
- **Method:** `GET`
- **Success Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "service": "naebak-gateway",
    "version": "1.0.0",
    "timestamp": "2025-09-26T12:00:00.000Z",
    "services_count": 12
  }
  ```

For more detailed monitoring, it is recommended to integrate with a monitoring solution like Prometheus and Grafana.

