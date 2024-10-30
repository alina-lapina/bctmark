# TICK Tech stack

## Telegraf
Telegraf is a plugin-driven server agent for collecting and reporting metrics. It is used to gather metrics from various sources, such as system metrics (CPU, memory, disk usage, etc.) and application metrics, and then send them to a specified output, such as InfluxDB.  

In the provided code snippets, Telegraf is configured to collect metrics from different inputs (like CPU, disk, memory, etc.) and send them to an InfluxDB instance. The configuration for Telegraf is specified in a template file (telegraf.conf.j2), which is likely rendered with specific values (e.g., collector_address) during deployment. 

Telegraf is part of the TICK stack (Telegraf, InfluxDB, Chronograf, and Kapacitor) and is commonly used for monitoring and logging purposes.
