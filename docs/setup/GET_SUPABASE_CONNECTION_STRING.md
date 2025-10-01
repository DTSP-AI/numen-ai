# How to Get Your Exact Supabase Connection String

We're getting a DNS resolution error, which means we need the **exact** connection string from your Supabase dashboard.

## Steps to Get Connection String

### 1. Go to Your Supabase Project Dashboard

https://supabase.com/dashboard/project/adkzlvblpxuqwhdwmvej

(Replace `adkzlvblpxuqwhdwmvej` with your actual project ID if different)

### 2. Navigate to Database Settings

- Click **Settings** (gear icon in sidebar)
- Click **Database**

### 3. Find Connection String Section

Scroll down to **Connection String** section

### 4. Select the Right Mode

You'll see several tabs:
- **URI** (what we need)
- **Postgres** (connection parameters)
- **JDBC**, **Golang**, etc.

**Click on "URI" tab**

### 5. Choose Connection Mode

You'll see options like:
- **Session Mode** (port 5432)
- **Transaction Mode** (port 6543)

**Choose "Session Mode" for now** (more compatible)

### 6. Copy the Full Connection String

It should look like:
```
postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@[HOST]:[PORT]/postgres
```

Example:
```
postgresql://postgres.adkzlvblpxuqwhdwmvej:MalayaisaBrat@2012@db.adkzlvblpxuqwhdwmvej.supabase.co:5432/postgres
```

### 7. Important: Check the Exact Format

The connection string should have:
- `postgres.[project-ref]` as username (with the dot!)
- Your password after the colon
- Host starting with `db.` or `aws-0-` depending on region
- Port `5432` for direct connection
- Database name `/postgres` at the end

### 8. Replace in `.env`

Once you have the exact string, replace the `SUPABASE_DB_URL` line in your `.env` file:

```bash
SUPABASE_DB_URL=postgresql://[PASTE-EXACT-CONNECTION-STRING-HERE]
```

## Common Issues & Fixes

### Issue 1: "getaddrinfo failed" (DNS resolution)
**Cause**: Wrong hostname format
**Fix**: Copy the exact connection string from Supabase dashboard

### Issue 2: "password authentication failed"
**Cause**: Wrong password in connection string
**Fix**: Verify password is exactly: `MalayaisaBrat@2012` (with @ symbol escaped if needed)

### Issue 3: "connection refused"
**Cause**: Network/firewall blocking Supabase
**Fix**: Check if your firewall allows outbound connections to Supabase

### Issue 4: "too many connections"
**Cause**: Hit connection limit
**Fix**: Use connection pooling (Transaction mode) or close other connections

## Alternative: Copy from Supabase Directly

If you have access to Supabase dashboard:

1. Settings → Database
2. Connection String → URI
3. **Session mode** or **Transaction mode**
4. Click **Copy** button
5. Replace `[YOUR-PASSWORD]` with: `MalayaisaBrat@2012`
6. Paste entire string into `.env`

## Test After Update

```bash
cd backend
python scripts/test_supabase_connection.py
```

You should see:
```
✅ Connected to PostgreSQL!
📊 Version: PostgreSQL 15.x...
```

---

**Once you have the exact connection string**, update `.env` and let me know - we'll test it immediately!
