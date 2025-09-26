> **Note:** This document is a work-in-progress and will be updated as the project evolves.

# Naebak Gateway: Developer Guide

**Version:** 1.0.0  
**Last Updated:** September 26, 2025  
**Author:** Manus AI

---

## 1. Service Overview

The **Naebak Gateway** is the entry point for all external traffic to the Naebak platform. It routes requests to the appropriate microservices, handles authentication, and provides a unified API for frontend applications.

### **Key Features:**

-   **Request Routing:** Routes incoming requests to the correct microservice.
-   **Authentication:** Verifies user authentication and authorization.
-   **Rate Limiting:** Protects services from abuse and denial-of-service attacks.
-   **CORS Handling:** Manages Cross-Origin Resource Sharing (CORS) for all services.

### **Technology Stack:**

-   **Framework:** Flask
-   **API Documentation:** Flask-RESTX (Swagger/OpenAPI)

---

## 2. Local Development Setup

### **Prerequisites:**

-   Python 3.11+
-   Pip

### **Installation:**

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/egyptofrance/naebak-gateway.git
    cd naebak-gateway
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**

    Create a `.env` file in the root directory and add the following:

    ```env
    SECRET_KEY=your-secret-key
    DEBUG=True
    ```

4.  **Start the development server:**

    ```bash
    python app.py
    ```

    The service will be available at `http://127.0.0.1:5000`.

---

## 3. Running Tests

To run the test suite, use the following command:

```bash
python -m pytest
```

---

## 4. API Documentation

The API documentation is available at the `/` endpoint, powered by Flask-RESTX.

---

## 5. Deployment

The service is designed to be deployed as a containerized application using Docker and Google Cloud Run. A `Dockerfile` is provided for building the container image.

---

## 6. Dependencies

Key dependencies are listed in the `requirements.txt` file.

---

## 7. Contribution Guidelines

Please follow the coding standards and pull request templates defined in the central documentation hub. All contributions must pass the test suite and include relevant documentation updates.
