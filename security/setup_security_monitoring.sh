#!/bin/bash

# 📊 Security Monitoring Setup for Dohodometr
# Настройка комплексного мониторинга security событий

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MONITORING_DIR="security/monitoring"
CONFIG_DIR="$MONITORING_DIR/config"
ALERTS_DIR="$MONITORING_DIR/alerts"
DASHBOARDS_DIR="$MONITORING_DIR/dashboards"

echo -e "${BLUE}📊 Security Monitoring Setup for Dohodometr${NC}"
echo "=================================================="

# Create directory structure
echo -e "${BLUE}📁 Creating monitoring directory structure...${NC}"
mkdir -p "$CONFIG_DIR"
mkdir -p "$ALERTS_DIR"  
mkdir -p "$DASHBOARDS_DIR"
mkdir -p "$MONITORING_DIR/scripts"

# 1. Prometheus Security Metrics Configuration
echo -e "${BLUE}🔧 Setting up Prometheus security metrics...${NC}"
cat > "$CONFIG_DIR/prometheus.yml" << 'EOF'
# Prometheus Configuration for Security Monitoring
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Application metrics
  - job_name: 'dohodometr-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'dohodometr-frontend'  
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # Redis metrics
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  # PostgreSQL metrics
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Nginx metrics
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']
EOF

# 2. Security Alerting Rules
echo -e "${BLUE}🚨 Creating security alerting rules...${NC}"
cat > "$ALERTS_DIR/security_alerts.yml" << 'EOF'
groups:
  - name: authentication_security
    rules:
      - alert: HighFailedLoginRate
        expr: rate(dohodometr_login_failed_total[5m]) > 5
        for: 2m
        labels:
          severity: high
          category: authentication
        annotations:
          summary: "High failed login rate detected"
          description: "Failed login rate is {{ $value }} attempts per second for the last 5 minutes"

      - alert: SuspiciousLoginPattern
        expr: dohodometr_login_attempts_per_ip > 10
        for: 1m
        labels:
          severity: critical
          category: authentication
        annotations:
          summary: "Suspicious login pattern detected"  
          description: "IP {{ $labels.ip }} has {{ $value }} login attempts in last minute"

      - alert: MultipleAccountLockouts
        expr: increase(dohodometr_account_lockouts_total[10m]) > 3
        for: 0m
        labels:
          severity: high
          category: authentication
        annotations:
          summary: "Multiple account lockouts detected"
          description: "{{ $value }} accounts locked in last 10 minutes"

  - name: api_security
    rules:
      - alert: HighAPIErrorRate
        expr: rate(dohodometr_http_requests_total{status_code=~"4xx|5xx"}[5m]) > 20
        for: 2m
        labels:
          severity: warning
          category: api
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value }} errors per second"

      - alert: UnauthorizedAccessAttempts
        expr: rate(dohodometr_http_requests_total{status_code="401"}[1m]) > 10
        for: 1m
        labels:
          severity: high
          category: api
        annotations:
          summary: "High unauthorized access attempts"
          description: "{{ $value }} unauthorized requests per second"

      - alert: SQLInjectionAttempt
        expr: increase(dohodometr_sql_injection_attempts_total[1m]) > 0
        for: 0m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "SQL injection attempt detected"
          description: "SQL injection attempt from IP {{ $labels.ip }}"

  - name: data_security  
    rules:
      - alert: UnusualDataAccess
        expr: rate(dohodometr_sensitive_data_access_total[5m]) > 100
        for: 3m
        labels:
          severity: high
          category: data
        annotations:
          summary: "Unusual sensitive data access pattern"
          description: "High rate of sensitive data access: {{ $value }} per second"

      - alert: DataEncryptionFailure
        expr: increase(dohodometr_encryption_failures_total[1m]) > 0
        for: 0m
        labels:
          severity: critical
          category: security
        annotations:
          summary: "Data encryption failure"
          description: "Encryption failure detected in service {{ $labels.service }}"

  - name: system_security
    rules:
      - alert: DiskSpaceUsage
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: warning
          category: system
        annotations:
          summary: "Low disk space"
          description: "Disk space usage is above 90%"

      - alert: MemoryUsage
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 10
        for: 5m
        labels:
          severity: warning
          category: system
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          category: system
        annotations:
          summary: "Service is down"
          description: "Service {{ $labels.job }} is down"
EOF

# 3. Grafana Security Dashboard
echo -e "${BLUE}📊 Creating Grafana security dashboard...${NC}"
cat > "$DASHBOARDS_DIR/security_dashboard.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Dohodometr Security Dashboard",
    "tags": ["security", "dohodometr"],
    "style": "dark",
    "timezone": "browser",
    "refresh": "30s",
    "schemaVersion": 27,
    "version": 1,
    "panels": [
      {
        "id": 1,
        "title": "Authentication Events",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(dohodometr_login_successful_total[5m])*60",
            "legendFormat": "Successful Logins/min"
          },
          {
            "expr": "rate(dohodometr_login_failed_total[5m])*60", 
            "legendFormat": "Failed Logins/min"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "palette-classic"},
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 10},
                {"color": "red", "value": 50}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "API Security Events",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(dohodometr_http_requests_total{status_code=\"401\"}[5m])",
            "legendFormat": "401 Unauthorized"
          },
          {
            "expr": "rate(dohodometr_http_requests_total{status_code=\"403\"}[5m])",
            "legendFormat": "403 Forbidden"
          },
          {
            "expr": "rate(dohodometr_http_requests_total{status_code=~\"5xx\"}[5m])",
            "legendFormat": "5xx Errors"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Geographic Login Distribution",
        "type": "geomap",
        "targets": [
          {
            "expr": "dohodometr_login_by_country",
            "legendFormat": "{{ country }}"
          }
        ],
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Active Security Alerts",
        "type": "table",
        "targets": [
          {
            "expr": "ALERTS{alertname=~\".*Security.*|.*Login.*|.*API.*\"}",
            "legendFormat": "{{ alertname }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 5,
        "title": "Data Access Patterns",
        "type": "heatmap",
        "targets": [
          {
            "expr": "dohodometr_sensitive_data_access_total",
            "legendFormat": "{{ endpoint }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "templating": {
      "list": []
    }
  }
}
EOF

# 4. Log Analysis Configuration (ELK Stack)
echo -e "${BLUE}📝 Setting up log analysis configuration...${NC}"
cat > "$CONFIG_DIR/logstash.conf" << 'EOF'
# Logstash Configuration for Security Log Analysis
input {
  beats {
    port => 5044
  }
  
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  # Parse application logs
  if [service] == "dohodometr-backend" {
    json {
      source => "message"
    }
    
    # Detect security events
    if [event] in ["login_failed", "login_successful", "2fa_failed", "account_locked"] {
      mutate {
        add_tag => ["security", "authentication"]
      }
    }
    
    if [event] in ["data_access", "sensitive_operation", "admin_action"] {
      mutate {
        add_tag => ["security", "data_access"] 
      }
    }
    
    # GeoIP enrichment
    if [ip_address] {
      geoip {
        source => "ip_address"
        target => "geoip"
      }
    }
    
    # Anomaly detection
    if [user_id] and [event] == "login_successful" {
      aggregate {
        task_id => "%{user_id}"
        code => "
          map['login_count'] ||= 0
          map['login_count'] += 1
          map['last_login'] = event.get('timestamp')
        "
        push_map_as_event_on_timeout => true
        timeout_task_id_field => "user_id"
        timeout => 300
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "dohodometr-security-%{+YYYY.MM.dd}"
  }
  
  # Send critical alerts to Slack
  if "critical" in [tags] {
    slack {
      url => "${SLACK_WEBHOOK_URL}"
      channel => "#security-alerts"
      username => "Security Bot"
      icon_emoji => ":warning:"
      format => "Security Alert: %{message}"
    }
  }
}
EOF

# 5. Security Monitoring Scripts
echo -e "${BLUE}🔍 Creating security monitoring scripts...${NC}"

# Real-time threat detection script
cat > "$MONITORING_DIR/scripts/threat_detection.py" << 'EOF'
#!/usr/bin/env python3
"""
Real-time Security Threat Detection for Dohodometr
Monitors logs and metrics for security threats
"""

import json
import time
import redis
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import requests

# Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
LOG_LEVEL = logging.INFO
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

# Threat detection thresholds
FAILED_LOGIN_THRESHOLD = 5  # per minute
API_ERROR_THRESHOLD = 20    # per minute
SUSPICIOUS_IP_THRESHOLD = 10 # requests per minute

class SecurityMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
        self.logger = self._setup_logging()
        self.failed_logins = defaultdict(deque)
        self.api_errors = defaultdict(deque)
        
    def _setup_logging(self):
        logging.basicConfig(
            level=LOG_LEVEL,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def check_failed_logins(self):
        """Check for suspicious login patterns"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=1)
        
        # Get failed login events from Redis
        failed_logins = self.redis_client.zrangebyscore(
            'failed_logins', 
            cutoff_time.timestamp(), 
            current_time.timestamp()
        )
        
        # Count by IP
        ip_counts = defaultdict(int)
        for event in failed_logins:
            event_data = json.loads(event)
            ip_counts[event_data['ip_address']] += 1
        
        # Alert on suspicious IPs
        for ip, count in ip_counts.items():
            if count >= FAILED_LOGIN_THRESHOLD:
                self._send_alert(
                    f"SECURITY ALERT: {count} failed login attempts from IP {ip} in last minute",
                    severity="HIGH"
                )
                
    def check_api_anomalies(self):
        """Check for API usage anomalies"""
        # Check for high error rates
        error_rate = self._get_metric('dohodometr_http_requests_total{status_code=~"4xx|5xx"}')
        if error_rate > API_ERROR_THRESHOLD:
            self._send_alert(
                f"SECURITY ALERT: High API error rate detected: {error_rate} errors/min",
                severity="MEDIUM"
            )
            
        # Check for unauthorized access attempts
        unauth_rate = self._get_metric('dohodometr_http_requests_total{status_code="401"}')
        if unauth_rate > SUSPICIOUS_IP_THRESHOLD:
            self._send_alert(
                f"SECURITY ALERT: High unauthorized access rate: {unauth_rate} attempts/min",
                severity="HIGH"
            )
    
    def _get_metric(self, query):
        """Get metric value from Prometheus"""
        try:
            response = requests.get(
                'http://prometheus:9090/api/v1/query',
                params={'query': f'rate({query}[1m])*60'}
            )
            data = response.json()
            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
        except Exception as e:
            self.logger.error(f"Error querying Prometheus: {e}")
        return 0
    
    def _send_alert(self, message, severity="MEDIUM"):
        """Send alert to Slack and log"""
        self.logger.warning(f"[{severity}] {message}")
        
        # Send to Slack
        try:
            payload = {
                'text': f"🚨 *{severity} SECURITY ALERT*\n{message}",
                'channel': '#security-alerts',
                'username': 'Security Monitor'
            }
            requests.post(SLACK_WEBHOOK_URL, json=payload)
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    def run(self):
        """Main monitoring loop"""
        self.logger.info("Starting security monitoring...")
        
        while True:
            try:
                self.check_failed_logins()
                self.check_api_anomalies()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.run()
EOF

chmod +x "$MONITORING_DIR/scripts/threat_detection.py"

# Log analysis script
cat > "$MONITORING_DIR/scripts/log_analyzer.sh" << 'EOF'
#!/bin/bash

# Security Log Analyzer for Dohodometr
# Analyzes application logs for security events

LOG_DIR="/var/log/dohodometr"
REPORT_FILE="/tmp/security_analysis_$(date +%Y%m%d_%H%M%S).txt"

echo "🔍 Security Log Analysis Report - $(date)" > "$REPORT_FILE"
echo "=================================================" >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# 1. Failed login analysis
echo "📊 FAILED LOGIN ANALYSIS" >> "$REPORT_FILE"
echo "Top 10 IP addresses with failed logins:" >> "$REPORT_FILE"
grep "login_failed" "$LOG_DIR"/*.log | \
    grep -o '"ip_address":"[^"]*"' | \
    cut -d'"' -f4 | \
    sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# 2. Suspicious API activity
echo "🌐 SUSPICIOUS API ACTIVITY" >> "$REPORT_FILE"
echo "Top endpoints with 4xx/5xx errors:" >> "$REPORT_FILE"
grep -E '"status_code":(4|5)[0-9][0-9]' "$LOG_DIR"/*.log | \
    grep -o '"path":"[^"]*"' | \
    cut -d'"' -f4 | \
    sort | uniq -c | sort -nr | head -10 >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# 3. Geographic analysis
echo "🌍 GEOGRAPHIC LOGIN ANALYSIS" >> "$REPORT_FILE"
echo "Login attempts by country:" >> "$REPORT_FILE"
grep "login_" "$LOG_DIR"/*.log | \
    grep -o '"country":"[^"]*"' | \
    cut -d'"' -f4 | \
    sort | uniq -c | sort -nr >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# 4. Time-based analysis
echo "⏰ TIME-BASED ANALYSIS" >> "$REPORT_FILE"
echo "Security events by hour (last 24h):" >> "$REPORT_FILE"
grep "$(date -d '24 hours ago' +%Y-%m-%d)" "$LOG_DIR"/*.log | \
    grep -E "(login_failed|unauthorized|security)" | \
    cut -d'T' -f2 | cut -d':' -f1 | \
    sort | uniq -c | sort -k2 >> "$REPORT_FILE"

echo >> "$REPORT_FILE"
echo "📄 Report saved to: $REPORT_FILE"
cat "$REPORT_FILE"
EOF

chmod +x "$MONITORING_DIR/scripts/log_analyzer.sh"

# 6. Docker Compose for monitoring stack
echo -e "${BLUE}🐳 Creating monitoring stack docker-compose...${NC}"
cat > "$MONITORING_DIR/docker-compose.monitoring.yml" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: dohodometr-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./alerts:/etc/prometheus/alerts:ro
      - prometheus_data:/prometheus
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: dohodometr-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./config/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    restart: unless-stopped
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: dohodometr-grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_INSTALL_PLUGINS=grafana-worldmap-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./dashboards:/var/lib/grafana/dashboards
    restart: unless-stopped
    networks:
      - monitoring

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    container_name: dohodometr-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - monitoring

  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    container_name: dohodometr-logstash
    volumes:
      - ./config/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
    environment:
      - "LS_JAVA_OPTS=-Xmx256m -Xms256m"
    networks:
      - monitoring
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    container_name: dohodometr-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    networks:
      - monitoring
    depends_on:
      - elasticsearch

  # Security monitoring service
  security-monitor:
    build:
      context: .
      dockerfile: Dockerfile.security-monitor
    container_name: dohodometr-security-monitor
    volumes:
      - ./scripts:/app/scripts
    environment:
      - REDIS_HOST=redis
      - PROMETHEUS_HOST=prometheus
    networks:
      - monitoring
    depends_on:
      - prometheus
      - redis

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
EOF

# 7. Alertmanager configuration
echo -e "${BLUE}📧 Creating alertmanager configuration...${NC}"
cat > "$CONFIG_DIR/alertmanager.yml" << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@dohodometr.ru'
  smtp_auth_username: 'alerts@dohodometr.ru'
  smtp_auth_password: 'your-smtp-password'

route:
  group_by: ['alertname', 'category']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: critical-alerts
  - match:
      category: authentication
    receiver: auth-alerts

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://localhost:5001/alerts'

- name: 'critical-alerts'
  email_configs:
  - to: 'security@dohodometr.ru'
    subject: '🚨 Critical Security Alert - {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#security-critical'
    title: 'Critical Security Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

- name: 'auth-alerts'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#security-alerts'
    title: 'Authentication Security Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
EOF

# 8. Create deployment script
echo -e "${BLUE}🚀 Creating deployment script...${NC}"
cat > "$MONITORING_DIR/deploy_monitoring.sh" << 'EOF'
#!/bin/bash

# Deploy Security Monitoring Stack

set -euo pipefail

echo "🚀 Deploying Dohodometr Security Monitoring Stack..."

# Check prerequisites
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is required but not installed"
    exit 1
fi

# Create necessary directories
mkdir -p data/prometheus
mkdir -p data/grafana
mkdir -p data/elasticsearch
mkdir -p logs

# Set permissions
sudo chown -R 1000:1000 data/grafana
sudo chown -R 1000:1000 data/elasticsearch

# Deploy monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Import Grafana dashboards
echo "📊 Importing Grafana dashboards..."
curl -X POST \
  http://admin:admin123@localhost:3001/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @dashboards/security_dashboard.json

echo "✅ Security monitoring stack deployed successfully!"
echo
echo "🔗 Access URLs:"
echo "  Prometheus:  http://localhost:9090"
echo "  Grafana:     http://localhost:3001 (admin/admin123)"
echo "  Kibana:      http://localhost:5601"
echo "  Alertmanager: http://localhost:9093"
echo
echo "📊 Next steps:"
echo "  1. Configure Slack webhooks in alertmanager.yml"
echo "  2. Set up email SMTP configuration"
echo "  3. Import additional dashboards"
echo "  4. Configure data retention policies"
EOF

chmod +x "$MONITORING_DIR/deploy_monitoring.sh"

# Final setup report
echo
echo -e "${GREEN}✅ Security Monitoring Setup Completed!${NC}"
echo "=================================================="
echo -e "${BLUE}📁 Created directories:${NC}"
echo "  - $MONITORING_DIR/config/ (configurations)"
echo "  - $MONITORING_DIR/alerts/ (alerting rules)"
echo "  - $MONITORING_DIR/dashboards/ (Grafana dashboards)"
echo "  - $MONITORING_DIR/scripts/ (monitoring scripts)"
echo
echo -e "${BLUE}🔧 Created configurations:${NC}"
echo "  - Prometheus metrics collection"
echo "  - Security alerting rules"
echo "  - Grafana security dashboard"
echo "  - ELK stack for log analysis"
echo "  - Real-time threat detection"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "  1. Configure Slack webhooks:"
echo "     Edit: $CONFIG_DIR/alertmanager.yml"
echo "  2. Deploy monitoring stack:"
echo "     Run: ./$MONITORING_DIR/deploy_monitoring.sh"
echo "  3. Start threat detection:"
echo "     Run: python3 $MONITORING_DIR/scripts/threat_detection.py"
echo "  4. Analyze logs:"
echo "     Run: ./$MONITORING_DIR/scripts/log_analyzer.sh"
echo
echo -e "${GREEN}🎉 Ready for production security monitoring!${NC}"
