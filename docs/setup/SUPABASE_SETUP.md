# Supabase Setup Guide for Numen AI

## Why Supabase?

Supabase provides a managed PostgreSQL database that eliminates the need for local database setup and solves the authentication issues we were experiencing. Benefits:

- ✅ No local PostgreSQL installation needed
- ✅ Free tier with 500MB database + 2GB bandwidth
- ✅ Automatic backups and management
- ✅ Built-in API and authentication (optional for future)
- ✅ Web-based SQL editor
- ✅ Real-time subscriptions (optional for future)

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up / Sign in
3. Click **"New Project"**
4. Fill in:
   - **Name**: `numen-ai` (or your preferred name)
   - **Database Password**: Create a strong password (save this!)
   - **Region**: Choose closest to you (e.g., `US West (Oregon)`)
   - **Pricing Plan**: Free tier is fine for development
5. Click **"Create new project"**
6. Wait 2-3 minutes for provisioning

## Step 2: Run Database Migration

1. In your Supabase dashboard, go to **Database > SQL Editor**
2. Click **"New Query"**
3. Copy the entire contents of `backend/supabase_migration.sql`
4. Paste into the SQL editor
5. Click **"Run"** (or press Ctrl+Enter)
6. You should see: `"Migration completed successfully!"`

## Step 3: Get Connection String

### Option A: Connection Pooler (Recommended for Production)

1. Go to **Project Settings** (gear icon in sidebar)
2. Click **Database** tab
3. Scroll to **Connection String** section
4. Select **"Connection pooler"** mode
5. Copy the connection string that looks like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```

### Option B: Direct Connection (Simpler for Development)

1. Same location as above
2. Select **"Direct connection"** mode
3. Copy the connection string that looks like:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

**Important**: Replace `[YOUR-PASSWORD]` with your actual database password

## Step 4: Update .env File

1. Open `backend/.env`
2. Find the line: `SUPABASE_DB_URL=`
3. Paste your connection string:
   ```env
   SUPABASE_DB_URL=postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   ```
4. Save the file

## Step 5: Test the Connection

1. Kill any running backend processes:
   ```bash
   # Windows
   taskkill /F /IM python.exe
   ```

2. Start the backend:
   ```bash
   cd backend
   python main.py
   ```

3. You should see:
   ```
   INFO - Connecting to Supabase PostgreSQL...
   INFO - Supabase PostgreSQL connection pool created
   INFO - Database tables initialized
   ```

4. Test the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

## Step 6: Test Intake Pipeline

1. Open frontend at `http://localhost:3002`
2. Fill out the intake form
3. Submit
4. Check Supabase dashboard:
   - Go to **Table Editor**
   - You should see `sessions` and `contracts` tables populated

## Verify Tables Created

In Supabase dashboard:

1. Go to **Table Editor** (table icon in sidebar)
2. You should see these tables:
   - `sessions`
   - `contracts`
   - `transcripts`
   - `manifestation_protocols`
   - `protocol_checkpoints`

## Troubleshooting

### "password authentication failed"

- Double-check you replaced `[YOUR-PASSWORD]` with actual password
- Make sure there are no extra spaces in the connection string
- Password in connection string must be URL-encoded (spaces = `%20`, etc.)

### "connection refused" or "timeout"

- Verify your Supabase project is active (green status in dashboard)
- Check your internet connection
- Try the "Direct connection" string instead of pooler

### "relation does not exist"

- The migration didn't run successfully
- Re-run the migration SQL script
- Check for errors in the SQL editor output

### RLS (Row Level Security) Issues

- If you get permission errors, the service role policy might not be working
- In Supabase dashboard, go to **Authentication > Policies**
- Verify "Service role can do anything" policies exist for each table
- You can temporarily disable RLS for testing:
  ```sql
  ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
  ```

## Optional: Update Docker Compose

Since you're using Supabase, you can remove the local PostgreSQL container:

1. Open `docker-compose.yml`
2. Comment out or remove the `postgres` service
3. Keep Redis and Qdrant (still needed for memory/caching)

```yaml
version: '3.8'

services:
  # postgres:  # <-- Comment this out
  #   image: postgres:16
  #   ...

  redis:
    image: redis:7-alpine
    # ... keep as is

  qdrant:
    image: qdrant/qdrant:v1.10.0
    # ... keep as is
```

## Next Steps

Once connected:

1. ✅ Backend on port 8000 should start successfully
2. ✅ Intake form submissions should work
3. ✅ Protocol generation can store to database
4. ✅ All CRUD operations functional

## Supabase Dashboard Features

Useful for development:

- **Table Editor**: Browse and edit data visually
- **SQL Editor**: Run custom queries
- **Database > Logs**: See query logs and errors
- **Database > Backups**: Automatic daily backups
- **API Docs**: Auto-generated REST/GraphQL APIs (if needed)

## Connection String Security

⚠️ **IMPORTANT**: Never commit your connection string to Git!

1. `.env` is already in `.gitignore`
2. Use environment variables in production
3. Rotate your database password if exposed

## Cost Considerations

**Free Tier Limits** (more than enough for development):
- 500 MB database space
- 2 GB bandwidth
- 50,000 monthly active users
- 500 MB file storage

When you exceed free tier, Supabase will notify you before charging.

## Production Deployment

For production, use environment variables:

```bash
# On your hosting platform (Render, Railway, Vercel, etc.)
SUPABASE_DB_URL=postgresql://postgres.xxxxx:password@...
```

Never hardcode in `.env` for production deployments.

---

**Questions?** Check [Supabase docs](https://supabase.com/docs/guides/database) or the backend logs for errors.
