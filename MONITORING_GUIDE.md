# 📊 Naebak Gateway - Monitoring System Guide

**Date:** September 26, 2025  
**Version:** 1.0.0  

---

## 🎯 **Overview**

The Naebak Gateway now includes a comprehensive monitoring system that provides real-time insights into gateway performance, service health, and system metrics. This system is built using industry-standard tools and practices.

### **Key Features**

- **Prometheus Metrics**: Comprehensive metrics collection for monitoring and alerting
- **Health Checking**: Advanced health monitoring with circuit breaker pattern
- **Structured Logging**: JSON-formatted logs with correlation IDs for request tracing
- **Performance Monitoring**: Request timing and performance categorization
- **Circuit Breakers**: Automatic failure detection and recovery

---

## 📈 **Metrics Collection**

### **Available Metrics**

| Metric Name | Type | Description |
|-------------|------|-------------|
| `gateway_requests_total` | Counter | Total number of requests processed |
| `gateway_request_duration_seconds` | Histogram | Request duration distribution |
| `gateway_active_connections` | Gauge | Current active connections |
| `gateway_service_health` | Gauge | Health status of backend services |
| `gateway_rate_limit_hits_total` | Counter | Rate limit violations |
| `gateway_auth_attempts_total` | Counter | Authentication attempts |
| `gateway_proxy_errors_total` | Counter | Proxy errors by service |

### **Accessing Metrics**

**Prometheus Format:**
```
GET /metrics
```

**Human-Readable Summary:**
```
GET /metrics/summary
```

**Example Response:**
```json
{
  "gateway_metrics": {
    "active_connections": 5,
    "total_requests": 1250
  },
  "health_metrics": {
    "total_services": 12,
    "healthy_services": 10,
    "health_percentage": 83.3
  }
}
```

---

## 🏥 **Health Monitoring**

### **Health Check Endpoints**

**Main Health Check:**
```
GET /health
```

**Detailed Services Health:**
```
GET /health/services
```

**Specific Service Health:**
```
GET /health/services?service=naebak-auth-service
```

### **Health Status Levels**

- **healthy**: All systems operational (≥80% services healthy)
- **degraded**: Some services experiencing issues (50-79% healthy)
- **unhealthy**: Critical services down (<50% healthy)

### **Circuit Breaker States**

- **CLOSED**: Normal operation, requests pass through
- **OPEN**: Service failures detected, requests blocked
- **HALF_OPEN**: Testing service recovery

---

## 🔍 **Structured Logging**

### **Log Format**

All logs are output in structured JSON format with the following fields:

```json
{
  "event": "request_completed",
  "logger": "request",
  "level": "info",
  "timestamp": "2025-09-26T05:28:43.223321Z",
  "service": "naebak-gateway",
  "version": "1.0.0",
  "correlation_id": "8d1b3253-2be2-4117-9d8e-11458d384cd5",
  "method": "GET",
  "path": "/health",
  "status_code": 200,
  "duration": 0.001594
}
```

### **Log Categories**

- **request**: HTTP request/response logging
- **performance**: Performance metrics and timing
- **security**: Authentication and authorization events
- **error**: Application errors and exceptions
- **business**: Business logic events

### **Correlation IDs**

Each request gets a unique correlation ID that tracks the request through all log entries, making it easy to trace request flows and debug issues.

---

## 🚨 **Circuit Breakers**

### **Configuration**

- **Failure Threshold**: 5 consecutive failures trigger circuit opening
- **Recovery Timeout**: 60 seconds before attempting recovery
- **Success Threshold**: 3 consecutive successes to close circuit

### **Monitoring Circuit Breakers**

```
GET /admin/circuit-breakers
Authorization: Bearer <admin-token>
```

**Example Response:**
```json
{
  "circuit_breakers": {
    "naebak-auth-service": {
      "state": "closed",
      "failure_count": 0,
      "success_count": 15
    },
    "naebak-messaging-service": {
      "state": "open",
      "failure_count": 5,
      "last_failure_time": "2025-09-26T05:20:00Z"
    }
  }
}
```

---

## 📊 **Performance Monitoring**

### **Performance Categories**

Requests are automatically categorized based on response time:

- **excellent**: < 100ms
- **good**: 100-500ms  
- **acceptable**: 500ms-1s
- **slow**: 1-2s
- **very_slow**: > 2s

### **Performance Metrics**

The system tracks:
- Request duration histograms
- Service call performance
- Error rates by service
- Authentication performance

---

## 🔧 **Setup and Configuration**

### **Prometheus Integration**

1. **Update prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'naebak-gateway'
    static_configs:
      - targets: ['localhost:8013']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

2. **Start Prometheus:**
```bash
prometheus --config.file=monitoring/prometheus.yml
```

### **Grafana Dashboards**

Create dashboards using these key metrics:
- Request rate: `rate(gateway_requests_total[5m])`
- Error rate: `rate(gateway_proxy_errors_total[5m])`
- Response time: `histogram_quantile(0.95, gateway_request_duration_seconds_bucket)`
- Service health: `gateway_service_health`

### **Log Aggregation**

For production, consider using:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Fluentd** for log collection
- **Grafana Loki** for log aggregation

---

## 🚀 **Best Practices**

### **Monitoring**

1. **Set up alerts** for critical metrics:
   - High error rates (>5%)
   - Slow response times (>2s for 95th percentile)
   - Service health degradation (<80%)
   - Circuit breaker activations

2. **Monitor trends** over time:
   - Request volume patterns
   - Performance degradation
   - Error rate increases

### **Logging**

1. **Use correlation IDs** to trace requests across services
2. **Log at appropriate levels**:
   - ERROR: System errors requiring attention
   - WARN: Potential issues or degraded performance
   - INFO: Normal operations and business events
   - DEBUG: Detailed debugging information

3. **Include context** in log messages:
   - User IDs for user actions
   - Service names for service calls
   - Request IDs for request tracing

### **Health Checks**

1. **Monitor circuit breaker states** regularly
2. **Set up automated recovery** procedures
3. **Test failure scenarios** to ensure circuit breakers work correctly

---

## 🔍 **Troubleshooting**

### **Common Issues**

**High Memory Usage:**
- Check for memory leaks in health checker threads
- Monitor metrics collection overhead
- Verify log rotation is working

**Circuit Breakers Not Working:**
- Check service health endpoints are responding
- Verify timeout configurations
- Review failure threshold settings

**Missing Metrics:**
- Ensure Prometheus Flask Exporter is properly initialized
- Check `/metrics` endpoint accessibility
- Verify metrics are being recorded in application code

### **Debug Commands**

```bash
# Check health status
curl http://localhost:8013/health

# Get detailed service health
curl http://localhost:8013/health/services

# View metrics summary
curl http://localhost:8013/metrics/summary

# Check circuit breaker states (requires auth)
curl -H "Authorization: Bearer <token>" http://localhost:8013/admin/circuit-breakers
```

---

## 📚 **References**

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Structured Logging Best Practices](https://www.structlog.org/)

---

**Last Updated:** September 26, 2025  
**Author:** Manus AI  
**Status:** Production Ready
