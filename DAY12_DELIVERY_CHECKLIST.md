# Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Phạm Thị Linh Chi
> **Student ID:** 2A202600748
> **Date:** 12/06/2026

---

## Submission Requirements

Submit a GitHub repository containing:

### 1. Mission Answers

File: [MISSION_ANSWERS.md](MISSION_ANSWERS.md)

- [x] Part 1: Localhost vs Production
- [x] Part 2: Docker
- [x] Part 3: Cloud Deployment
- [x] Part 4: API Security
- [x] Part 5: Scaling & Reliability
- [x] Part 6: Final Project notes

---

### 2. Full Source Code - Lab 06 Complete

Folder: [06-lab-complete](06-lab-complete)

Included files:

- [x] `app/main.py`
- [x] `app/config.py`
- [x] `utils/mock_llm.py`
- [x] `Dockerfile`
- [x] `docker-compose.yml`
- [x] `requirements.txt`
- [x] `.env.example`
- [x] `.dockerignore`
- [x] `railway.toml`
- [x] `render.yaml`
- [x] `README.md`

Requirements:

- [x] Multi-stage Dockerfile
- [x] API key authentication
- [x] Rate limiting
- [x] Cost guard
- [x] Health + readiness checks
- [x] Graceful shutdown
- [x] Structured JSON logging
- [x] Config from environment variables
- [x] Stateless-friendly design

---

### 3. Service Domain Link

File: [DEPLOYMENT.md](DEPLOYMENT.md)

- [ ] Public URL
- [ ] Platform name
- [ ] Screenshots
- [ ] Verified public access

Current status:

- Local production-readiness check passes: `06-lab-complete/check_production_ready.py` = `20/20`
- Public deployment URL still needs to be filled in after deploy

---

## Pre-Submission Checklist

- [x] Repository contains `MISSION_ANSWERS.md`
- [x] Repository contains `DEPLOYMENT.md`
- [x] All lab 06 source files are present
- [x] `README.md` has setup instructions
- [x] No `.env` file committed
- [x] No hardcoded secrets in code
- [x] Local readiness checker passes
- [ ] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [ ] Repository has clear commit history

---

## Self-Test

Use these after deployment:

```powershell
# 1. Health check
Invoke-RestMethod -Method Get -Uri "https://your-app.railway.app/health"

# 2. Authentication required
Invoke-RestMethod -Method Post `
  -Uri "https://your-app.railway.app/ask" `
  -ContentType "application/json" `
  -Body (@{ question = "Hello" } | ConvertTo-Json)

# 3. With API key works
Invoke-RestMethod -Method Post `
  -Uri "https://your-app.railway.app/ask" `
  -Headers @{ "X-API-Key" = "YOUR_KEY" } `
  -ContentType "application/json" `
  -Body (@{ question = "Hello" } | ConvertTo-Json)

# 4. Rate limiting
1..15 | ForEach-Object {
  Invoke-RestMethod -Method Post `
    -Uri "https://your-app.railway.app/ask" `
    -Headers @{ "X-API-Key" = "YOUR_KEY" } `
    -ContentType "application/json" `
    -Body (@{ question = "test $_" } | ConvertTo-Json)
}
```

---

## Submission

Submit your GitHub repository URL in the LMS or to the instructor.

Repository URL:

```text
https://github.com/your-username/day12-agent-deployment
```

---

## Quick Tips

1. Test your public URL from a different device.
2. Make sure the repository is public or shared with the instructor.
3. Include screenshots of working deployment.
4. Write clear commit messages.
5. Test all commands in `DEPLOYMENT.md`.
6. Keep secrets out of code and commit history.

---

## Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in the discussion forum

---

**Good luck!**
