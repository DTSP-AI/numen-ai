# 🚨 SECURITY QUICK REFERENCE
**HypnoAgent Production Readiness - Critical Actions**

---

## ⚠️ IMMEDIATE SECURITY ALERTS

### 🔴 STOP: Do Not Deploy to Production
This application has **CRITICAL security vulnerabilities** that prevent safe deployment.

**Production Readiness Score: 52/100**
**Recommendation: NO-GO**

---

## 🚨 EMERGENCY ACTIONS (TODAY)

### 1. Secrets Emergency
```bash
# CHECK: Are secrets in git history?
git log --all -- '*.env'
git log --all | grep -E 'api_key|secret|password' -i

# IF FOUND: Clean git history
git filter-repo --path .env --invert-paths
git filter-repo --path backend/.env --invert-paths

# ROTATE ALL API KEYS IMMEDIATELY:
# - OpenAI API key
# - ElevenLabs API key
# - LiveKit credentials
# - Database passwords
```

### 2. Block Production Deployment
- Add deployment gate requiring security approval
- No deployments until authentication implemented
- No deployments until secrets management implemented

---

## 🔐 Top 5 Critical Security Issues

### 1. NO AUTHENTICATION ❌
**Impact:** Any user can access/modify all data

**Location:** All endpoints
**Fix Required:** Implement JWT authentication (Week 2-3)

### 2. SECRETS EXPOSED ❌
**Impact:** API keys may be compromised

**Location:** `.env` files, `docker-compose.yml`
**Fix Required:** Secrets management service (Week 1)

### 3. WIDE-OPEN CORS ❌
**Impact:** CSRF attacks, session hijacking

**Location:** `backend/main.py:52-59`
**Fix Required:** Restrict CORS (Week 4)

### 4. NO RATE LIMITING ❌
**Impact:** API abuse, cost explosion

**Location:** All endpoints
**Fix Required:** Implement rate limiting (Week 5)

### 5. FILE UPLOAD VULNERABILITIES ❌
**Impact:** Malware upload, XSS attacks

**Location:** `backend/routers/avatar.py:111-168`
**Fix Required:** Secure file upload (Week 6)

---

## 🛡️ Security Checklist (Before ANY Deployment)

### Authentication
- [ ] JWT authentication implemented on ALL endpoints
- [ ] No hardcoded default user/tenant IDs
- [ ] Token expiration configured (15 min)
- [ ] Refresh token rotation implemented

### Authorization
- [ ] Tenant isolation enforced
- [ ] Role-based access control (RBAC)
- [ ] Permission checking on data access

### Secrets Management
- [ ] No secrets in code or docker-compose
- [ ] Secrets management service configured
- [ ] All API keys rotated
- [ ] .env files removed from repository

### Input Validation
- [ ] All user inputs validated
- [ ] File uploads validated (magic numbers)
- [ ] Prompt injection protection
- [ ] SQL injection protection verified

### Security Headers
- [ ] CORS properly restricted
- [ ] HSTS enabled
- [ ] CSP configured
- [ ] X-Frame-Options: DENY
- [ ] CSRF protection implemented

### Rate Limiting
- [ ] General endpoints: 100 req/min
- [ ] AI endpoints: 10 req/min
- [ ] File uploads: 5 req/hour
- [ ] Rate limits per authenticated user

### Monitoring
- [ ] Error tracking (Sentry) configured
- [ ] Security audit logging enabled
- [ ] Alerts for failed authentication
- [ ] Alerts for rate limit violations

---

## 📋 Quick Security Self-Assessment

Run this before any deployment:

```bash
# 1. Check for secrets in code
grep -r "api_key\|secret\|password" backend/ --include="*.py" | grep -v ".env.example"

# 2. Check for hardcoded credentials
grep -r "changeme\|password123\|secret123" .

# 3. Check if .env in git
git ls-files | grep ".env"

# 4. Check authentication on endpoints
grep -r "@router" backend/routers/ | wc -l
# Compare with authenticated endpoints count

# 5. Check CORS configuration
grep -A 5 "CORSMiddleware" backend/main.py
```

**If ANY check fails → DO NOT DEPLOY**

---

## 🔍 Code Review Security Checklist

When reviewing code, check for:

### ❌ NEVER Allow
- [ ] Hardcoded secrets or API keys
- [ ] SQL string concatenation
- [ ] `eval()` or `exec()` calls
- [ ] Unrestricted file uploads
- [ ] Endpoints without authentication
- [ ] User input in file paths
- [ ] PII/PHI in log statements

### ✅ ALWAYS Require
- [ ] Parameterized database queries
- [ ] Input validation with Pydantic
- [ ] Authentication decorator on endpoints
- [ ] Error handling (try/except)
- [ ] Proper logging (no sensitive data)
- [ ] Type hints on functions
- [ ] Unit tests for new code

---

## 🚦 Deployment Gates

### Cannot Deploy Until:
1. ✅ Authentication implemented on ALL endpoints
2. ✅ All secrets moved to secrets management
3. ✅ CORS configuration fixed
4. ✅ Rate limiting implemented
5. ✅ Security headers configured
6. ✅ File upload security implemented
7. ✅ Monitoring and alerting operational
8. ✅ Test coverage ≥ 50%
9. ✅ Security audit passed
10. ✅ Legal/compliance approval (if handling PHI)

---

## 📞 Security Incident Response

### If You Discover a Security Issue:

1. **DO NOT** commit the fix publicly yet
2. **DO** notify security team immediately
3. **DO** assess impact and exposure
4. **DO** rotate credentials if compromised
5. **DO** document the incident
6. **THEN** fix and deploy

### Security Team Contacts
- Security Lead: [TBD]
- Engineering Manager: [TBD]
- Legal/Compliance: [TBD]

---

## 📚 Required Reading

### Before Writing Code
- [ ] OWASP Top 10: https://owasp.org/www-project-top-ten/
- [ ] FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- [ ] Python Security Best Practices

### Before Deploying
- [ ] Full Audit Report: `docs/architecture/PRODUCTION_READINESS_AUDIT.yaml`
- [ ] Summary: `docs/architecture/PRODUCTION_READINESS_SUMMARY.md`
- [ ] Remediation Checklist: `docs/architecture/REMEDIATION_CHECKLIST.md`

---

## 🎯 Sprint Priorities (Next 8 Weeks)

### Sprint 1-2 (Weeks 1-4): Critical Security
- Authentication/Authorization
- Secrets management
- CORS and security headers

### Sprint 3-4 (Weeks 5-8): Security Hardening
- Rate limiting
- File upload security
- Audit logging

### Sprint 5-6 (Weeks 9-12): Infrastructure
- Monitoring (Sentry, Prometheus)
- Testing framework (pytest)
- Database migrations (Alembic)

### Sprint 7-8 (Weeks 13-16): Production Prep
- CI/CD pipeline
- Load testing
- Performance optimization

---

## 🔧 Quick Fixes (Copy-Paste Ready)

### Add Authentication Dependency
```python
from fastapi import Depends, HTTPException
from backend.middleware.auth import get_current_user
from backend.models.user import User

@router.get("/agents")
async def list_agents(current_user: User = Depends(get_current_user)):
    # Now protected by authentication
    pass
```

### Add Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/protocols/generate")
@limiter.limit("10/minute")
async def generate_protocol(request: Request, ...):
    pass
```

### Fix CORS (Production)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # Single origin
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)
```

### Add Security Headers
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[os.getenv("ALLOWED_HOST")]
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

---

## ⚖️ HIPAA Compliance Quick Check

If handling Protected Health Information (PHI):

- [ ] Encryption at rest enabled
- [ ] Encryption in transit (HTTPS) enforced
- [ ] Audit logging for all PHI access
- [ ] Access controls implemented
- [ ] Data retention policy defined
- [ ] Consent management implemented
- [ ] BAA (Business Associate Agreement) process
- [ ] NO PHI in application logs
- [ ] Account deletion capability
- [ ] Data export capability (GDPR)

**If ANY item unchecked → Cannot handle PHI**

---

## 🎓 Training Resources

### For All Developers
- OWASP Top 10: 30 min
- FastAPI Security Tutorial: 1 hour
- Git Secrets Prevention: 30 min

### For Backend Team
- Authentication Best Practices: 2 hours
- Database Security: 1 hour
- API Security: 2 hours

### For DevOps Team
- Secrets Management: 2 hours
- Container Security: 2 hours
- Monitoring & Alerting: 2 hours

---

## 📊 Current Status Summary

**Overall Security Grade: F**
**Production Ready: NO**
**Estimated Time to Production: 16-24 weeks**

### Critical Issues: 12
### High Priority Issues: 15
### Medium Priority Issues: 8

**Next Milestone:** Complete Phase 1 (Security Fundamentals) - Week 8

---

## 🚀 Getting Started (Week 1)

```bash
# Clone repo (if not already)
git clone <repo-url>
cd AffirmationApplication

# Check for secrets in history
git log --all -- '*.env'

# Install dependencies
cd backend
pip install -r requirements.txt

# Read documentation
cat docs/architecture/PRODUCTION_READINESS_SUMMARY.md
cat docs/architecture/REMEDIATION_CHECKLIST.md

# Create feature branch
git checkout -b feature/authentication

# Start coding (Week 2 work)
# See REMEDIATION_CHECKLIST.md for detailed tasks
```

---

## ⚡ Remember

1. **Security is not optional** - It's a deployment blocker
2. **Test everything** - Especially authentication and authorization
3. **Never commit secrets** - Use secrets management services
4. **Default deny** - Require authentication unless explicitly public
5. **Monitor everything** - You can't fix what you can't see

---

**Last Updated:** October 2, 2025
**Next Review:** Weekly (Mondays)

**Questions?** See full documentation in `docs/architecture/`
