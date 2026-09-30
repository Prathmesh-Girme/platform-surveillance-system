# PlatformSurveillance

A lightweight, background-ready system telemetry and process surveillance automation engine written in Python. It periodically monitors operational system health—including CPU utilization across active cores, RAM allocation, network bandwidth I/O, and active process states—and captures all diagnostic telemetry into structured, timestamped audit logs for administrative analysis and system performance evaluation.

---

## 💡 System Motivation & Objective

Maintaining continuous operational visibility into system performance and active process behavior is critical for server reliability and proactive troubleshooting. 

This automation utility was developed to address key operational needs:
- **Diagnostic Audit Trail**: Raw telemetry data captured in real time enables post-event investigation of CPU/RAM spikes, memory leaks, and process crashes.
- **Resource Bottleneck Detection**: Tracking virtual memory consumption and network I/O helps identify background processes consuming excessive system resources.
- **Automated Health Monitoring**: Eliminates manual intervention by scheduling background surveillance loops that log non-blocking diagnostic reports automatically.

---

## ⚙️ Execution Architecture