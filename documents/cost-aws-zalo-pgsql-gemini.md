# **Retail Chatbot** in **AWS Mumbai (ap-south-1)** for **100K customer profiles** and **500 concurrent users (CCU)**
Here’s the **full, updated monthly cost estimate** for running your **Retail Chatbot architecture** in **AWS Mumbai** using **Aurora PostgreSQL 16 Serverless v2**, with **100K profiles** and **500 concurrent users (CCU)**.

---

## 🛠️ System Architecture Recap

```
Zalo User
   ↓ (chat message)
Zalo Webhook → API Gateway → Lambda Handler (Webhook Processor)
   ↓
[1] Validate & Parse message
   ↓
[2] Query Aurora PGSQL 16 (pgvector) for context + retrieve docs
   ↓
[3] Check Redis cache for query/response
   ↓
[4] If cache miss → build prompt + call Gemini API
   ↓
[5] Save response in Redis cache + optionally log conversation
   ↓
[6] Lambda returns response → API Gateway → Zalo API → User
```

---

## 📦 Component-Wise Monthly Cost Estimate

| Component                              | Assumptions and Notes                                                  | Monthly Cost (USD) |
| -------------------------------------- | ---------------------------------------------------------------------- | ------------------ |
| **Aurora PostgreSQL 16 Serverless v2** | 1.5 ACU avg usage × 730 hrs; 15 GB storage; \~2M I/O ops               | \~\$133.45         |
| **Amazon ElastiCache (Redis)**         | `cache.t3.small` (1 vCPU, 2GB RAM) + 10 GB data + VPC traffic          | \~\$33             |
| **AWS Lambda**                         | 300K invocations/month; 512 MB memory; 300ms avg duration              | \~\$1              |
| **Amazon API Gateway**                 | 300K requests/month (REST)                                             | \~\$1.05           |
| **Google Gemini API** (via REST)       | \~60K calls/month (20% cache miss), avg 800 tokens/call → \~48M tokens | \~\$12             |
| **Zalo API**                           | No cost                                                                | \$0                |

---

## ✅ **Total Estimated Cost (Monthly)**

| **Total Services** | **\~\$180.50/month** |
| ------------------ | -------------------- |

This includes everything needed to serve **500 concurrent Zalo users**, query 100K profiles, support **real-time vector search**, do **RAG with Gemini**, and **cache responses**.

---

## 💡 Cost Optimization Tips

| Area       | Tip                                                                 |
| ---------- | ------------------------------------------------------------------- |
| **Aurora** | Set **min ACU = 0.5** or use **RDS Proxy** to reduce idle ACU usage |
| **Gemini** | Increase **cache hit rate to >90%** by smart query normalization    |
| **Redis**  | Use **LRU + TTL** to prune cold entries; avoid overprovisioning     |
| **Lambda** | Optimize memory-to-duration ratio for lower execution cost          |
| **API**    | Bundle messages in fewer calls if UX allows                         |

---

## ⚙️ Optional Add-ons (Optional Costs)

| Add-on                             | Cost Estimate | Notes                                          |
| ---------------------------------- | ------------- | ---------------------------------------------- |
| CloudWatch (Lambda logs & metrics) | \~\$5–10      | Depends on volume of logs and retention period |
| RDS Proxy for Aurora               | \~\$15–20     | Optional, reduces connection overhead          |
| S3 backup of logs/conversations    | \~\$1–2       | If you want to archive chat history cheaply    |

---

## 📊 Ready for Scaling?

This setup will **scale to 1M profiles and \~2K CCU** with minimal refactoring. For that scale:

* Upgrade Redis to `cache.t3.medium`
* Consider adding `pgbouncer` or partitioning strategies in Aurora
* Set up autoscaling thresholds in Aurora Serverless


