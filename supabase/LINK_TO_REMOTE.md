# Link Local Supabase to Remote Project

## Quick Steps

### 1. Login to Supabase
```bash
npx supabase login
```

This will:
- Display a device code (e.g., `ABCD-EFGH`)
- Open your browser to https://supabase.com/activate
- Ask you to enter the code
- Authenticate your CLI

### 2. Link to Existing Project
```bash
npx supabase link --project-ref vcexixyxquecgxkhttgl
```

**What this does:**
- Connects your local `supabase/` directory to the remote project
- Creates `supabase/.temp/project-ref` file
- Allows pushing/pulling migrations

### 3. Pull Current Remote Schema (Optional but Recommended)
```bash
npx supabase db pull
```

**What this does:**
- Downloads your current remote database schema
- Saves it as a migration file in `supabase/migrations/`
- Shows you what's currently in production
- Helps identify conflicts before pushing

**Expected Output:**
```
Pulling schema from remote database...
Creating migration: supabase/migrations/20251013_remote_schema.sql
```

### 4. Review What Will Be Pushed
```bash
npx supabase db diff
```

**What this does:**
- Compares local migrations to remote schema
- Shows SQL statements that will be executed
- Lets you preview changes before applying

### 5. Push New Migrations to Remote
```bash
npx supabase db push
```

**What this does:**
- Applies our 2 new migration files to your remote database:
  - `20250101000000_initial_schema.sql`
  - `20250101000001_cognitive_assessment.sql`
- Creates tables: `goal_assessments`, `belief_graphs`, `cognitive_metrics`, `cognitive_schema_versions`
- Extends `user_discovery` table with 4 new columns

**⚠️ IMPORTANT:** This modifies your production database. Review the diff first!

---

## Alternative: Use Access Token

If device code flow doesn't work:

### 1. Get Access Token
- Go to https://supabase.com/dashboard/account/tokens
- Click "Generate new token"
- Copy the token

### 2. Add to `.env`
```bash
SUPABASE_ACCESS_TOKEN=sbp_your_token_here
```

### 3. Run Commands
```bash
npx supabase link --project-ref vcexixyxquecgxkhttgl
npx supabase db pull
npx supabase db diff
npx supabase db push
```

---

## Verification Steps

After pushing migrations:

### 1. Check Supabase Studio
- Go to https://vcexixyxquecgxkhttgl.supabase.co
- Navigate to "Table Editor"
- Verify new tables exist:
  - `goal_assessments`
  - `belief_graphs`
  - `cognitive_metrics`
  - `cognitive_schema_versions`

### 2. Check Existing Tables
- Verify `user_discovery` has 4 new columns:
  - `cognitive_assessment_completed`
  - `gas_scores`
  - `belief_graph_id`
  - `intake_depth`

### 3. Run Test Query
```sql
SELECT version, description, is_active
FROM cognitive_schema_versions
WHERE is_default = TRUE;
```

Expected result:
```
v1.0 | Default Cognitive Kernel v1.0 - Foundational goal/belief assessment framework | TRUE
```

---

## Rollback (If Needed)

If something goes wrong:

```bash
# Reset remote database to previous state
npx supabase db reset --remote
```

**⚠️ WARNING:** This will drop ALL data in your remote database!

Better approach - create a backup first:
```bash
npx supabase db dump > backup_$(date +%Y%m%d).sql
```

---

## Expected Timeline

- Login: 30 seconds
- Link: 5 seconds
- Pull schema: 10-30 seconds
- Review diff: 2-5 minutes (manual review)
- Push migrations: 30-60 seconds

**Total:** ~5 minutes

---

## Troubleshooting

### Error: "Database does not exist"
**Solution:** Create the database first in Supabase dashboard

### Error: "Migration already exists"
**Solution:** Skip the migration or reset local database

### Error: "Connection refused"
**Solution:** Check your `SUPABASE_DB_URL` in `.env`

### Error: "Foreign key constraint violation"
**Solution:** Your remote database might have existing data that conflicts. Review with `db pull` first.

---

## What Happens to Existing Data?

**Safe Operations:**
- Creating new tables: ✅ No impact on existing data
- Adding columns with defaults: ✅ Existing rows get default values
- Creating indexes: ✅ No data loss, just slower migration

**Risky Operations:**
- None in our migrations! All operations are additive.

---

## Post-Migration Checklist

After successful push:

- [ ] Verify new tables exist in Supabase Studio
- [ ] Check `user_discovery` table has new columns
- [ ] Run test query to confirm data seeding
- [ ] Update application `.env` if needed
- [ ] Test application against remote database
- [ ] Run backend test suites
- [ ] Monitor error logs for 24 hours

---

## Next Steps After Sync

1. **Update Application:**
   ```bash
   # Your app should already be using SUPABASE_DB_URL from .env
   # No code changes needed if using database.py
   ```

2. **Remove Inline Schema (Optional):**
   - Migrations now manage schema
   - Can remove CREATE TABLE statements from `database.py`
   - Keep connection pool logic

3. **Test Cognitive Features:**
   ```bash
   pytest backend/tests/test_memory_cognitive.py -v
   pytest backend/tests/test_cognitive_intake.py -v
   ```

4. **Deploy Backend:**
   - Cognitive functions are now available
   - Agents can start using cognitive assessment
   - Reflex triggers will activate on thresholds

---

## Support

If you encounter issues:
1. Check Supabase logs: https://vcexixyxquecgxkhttgl.supabase.co/project/logs
2. Check migration history: `npx supabase migration list`
3. Review this guide's troubleshooting section
4. Contact Supabase support if needed

---

**Ready to proceed? Run the commands above in order!**
