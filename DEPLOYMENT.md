# Deployment Information

## Public URL
TBD - add your deployed Railway or Render URL here.

## Platform
Railway / Render / Cloud Run

## Local Verification
- Production readiness checker: `06-lab-complete/check_production_ready.py`
- Result: 20/20 checks passed

## Test Commands

### Health Check
```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/health"
```

### API Test
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:8000/ask" `
  -Headers @{ "X-API-Key" = "YOUR_KEY" } `
  -ContentType "application/json" `
  -Body (@{ question = "Hello" } | ConvertTo-Json)
```

## Environment Variables
- HOST
- PORT
- ENVIRONMENT
- DEBUG
- APP_NAME
- APP_VERSION
- OPENAI_API_KEY
- LLM_MODEL
- AGENT_API_KEY
- JWT_SECRET
- RATE_LIMIT_PER_MINUTE
- DAILY_BUDGET_USD
- REDIS_URL
- ALLOWED_ORIGINS

## Screenshots
Add screenshots after deployment:
- Dashboard
- Service running
- Health check
- API request test
