# How to Use the External API Sync Validator Agent

This guide shows you how to invoke and use the External API Sync Validator agent in your development workflow.

## Quick Start

### Method 1: Manual Invocation via Task Tool

When you make changes to code that affects External API integration, you can manually invoke the agent:

```
You: I just added a new endpoint to delete schedules. Can you validate the External API sync?

Claude: I'll use the Task tool to invoke the external-api-sync-validator agent...
```

**When to use this method:**
- After implementing new features that interact with Crossmark API
- When you want a detailed validation report before committing
- During code review to validate sync integrity
- When debugging sync issues

### Method 2: Request Validation for Specific Files

```
You: I modified routes/api.py to add bulk scheduling. Please run the External API sync validator on these changes.

Claude: I'll invoke the external-api-sync-validator agent to validate your changes to routes/api.py...
```

### Method 3: Automatic Validation (Recommended for Regular Use)

You can request the agent to automatically validate sync-related changes:

```
You: From now on, whenever I make changes to routes/api.py, routes/scheduling.py, or any model files, automatically run the External API sync validator before committing.

Claude: I'll set up automatic validation for those files...
```

## Example Validation Sessions

### Example 1: Validating a New Schedule Endpoint

```
You: I added a new endpoint `/api/schedules/bulk-create` that creates multiple schedules at once. Here's the code:
[paste code]
Please validate the External API sync.

Claude: I'll invoke the external-api-sync-validator agent to analyze this bulk creation endpoint...

[Agent generates validation report]

Agent Report:
✅ PASSED: External API calls present for each schedule
⚠️ WARNING: Missing error handling if one schedule fails mid-batch
❌ FAILED: external_id not stored after successful API call

Recommendations:
1. Add transaction rollback for partial failures
2. Store scheduleEventID in Schedule.external_id after each successful call
3. Update sync_status field appropriately

Would you like me to implement these fixes?
```

### Example 2: Code Review Validation

```
You: I'm reviewing a PR that modifies the schedule deletion logic. Can you run the sync validator on commit abc123?

Claude: I'll check out that commit and run the external-api-sync-validator...

[Agent generates validation report]

Agent Report:
✅ PASSED: Calls session_api.unschedule_mplan_event()
✅ PASSED: Proper error handling implemented
✅ PASSED: Uses correct external_id (scheduleEventID)
⚠️ WARNING: No check if schedule already unscheduled in Crossmark

Status: APPROVED with minor recommendation
```

### Example 3: Debugging Sync Issues

```
You: We have schedules in our database that don't exist in Crossmark. Can the sync validator help identify the problem?

Claude: I'll invoke the external-api-sync-validator agent in diagnostic mode...

[Agent analyzes codebase and database]

Agent Report:
Found 15 schedules with sync_status='failed'

Root cause analysis:
- Schedules created in routes/scheduling.py:245
- Missing session_api.schedule_mplan_event() call
- Bug introduced in commit def456

Recommendation: Add API call at line 250 before db.session.commit()
```

## Understanding Validation Reports

The agent generates structured reports with three severity levels:

### ✅ Passed Checks
These are things the agent verified are correct:
- External API calls are present
- Authentication is handled properly
- Error handling is implemented
- Field mappings are correct

**Action:** No action needed, these are good!

### ⚠️ Warnings
These are potential issues that won't break functionality but could cause problems:
- Missing validation that could prevent errors
- Suboptimal error handling
- Missing sync_status tracking
- Potential race conditions

**Action:** Consider addressing these before merging, but not blocking

### ❌ Failed Checks
These are critical issues that will cause sync problems:
- Missing External API calls
- Using wrong field names
- No error handling
- external_id not being stored

**Action:** Must fix before merging code

## Common Validation Scenarios

### Scenario 1: Adding a New Schedule Creation Endpoint

**What the agent checks:**
- ✅ Calls `session_api.schedule_mplan_event()`
- ✅ Stores `scheduleEventID` as `schedule.external_id`
- ✅ Updates `sync_status` to 'synced'
- ✅ Handles API errors
- ✅ Uses correct field mappings (store_number, location_mvid)
- ✅ Validates external_ids exist before API call

**Common issues detected:**
- Missing API call (only saves to local DB)
- Not storing external_id returned by API
- Using wrong field (e.g., event.store_id instead of event.store_number)

### Scenario 2: Modifying Event Model

**What the agent checks:**
- ✅ external_id field preserved
- ✅ Field mappings still correct in sync_engine.py
- ✅ No conflicts with Crossmark field names
- ✅ Migration doesn't break external_id tracking

**Common issues detected:**
- Renaming external_id field
- Adding field with same name as Crossmark field
- Missing migration

### Scenario 3: Updating Sync Engine

**What the agent checks:**
- ✅ Bidirectional sync still functional
- ✅ Date parsing handles all formats
- ✅ Field mappings accurate
- ✅ Error handling for all API calls
- ✅ Bulk operations don't exceed rate limits

**Common issues detected:**
- Breaking field mappings
- Not handling new Crossmark response formats
- Missing timezone conversion

## Tips for Best Results

### 1. Provide Context
```
You: I'm adding a feature to reassign schedules to different employees.
This will delete the old schedule in Crossmark and create a new one.
Please validate the sync logic.
```

Better than just: "Validate this code"

### 2. Specify What Changed
```
You: I modified routes/api.py lines 500-600 to add error retry logic.
Please validate that this doesn't break the External API sync.
```

### 3. Ask for Specific Checks
```
You: I want to verify that my new bulk scheduler properly:
1. Calls the API for each schedule
2. Handles partial failures
3. Stores external_ids correctly

Please run the sync validator with focus on these points.
```

### 4. Request Follow-up Actions
```
You: After validating, if you find issues, please:
1. Generate the validation report
2. Implement the recommended fixes
3. Re-run validation to confirm fixes
```

## Integration with Git Workflow

### Pre-Commit Validation
```bash
# Before committing sync-related changes:
You: I'm about to commit changes to routes/api.py.
     Please run the sync validator and only proceed with commit if validation passes.

Claude: Running external-api-sync-validator...
        [validation report]
        ✅ All checks passed. Proceeding with commit...
```

### Pre-Push Validation
```bash
# Before pushing to remote:
You: I'm ready to push my feature branch.
     Please validate all sync-related changes I made in this branch.

Claude: Analyzing changes since branching from main...
        [comprehensive validation report for all changes]
```

### Code Review Assistance
```bash
You: I'm reviewing PR #123. Please run the sync validator on all changed files.

Claude: [validates PR changes and generates report]
```

## Troubleshooting

### Agent Not Finding Issues You Know Exist

**Possible causes:**
1. Agent is analyzing old code (run `git pull` first)
2. Issue is in file not being analyzed (specify file explicitly)
3. Agent's validation rules need updating

**Solution:**
```
You: The agent didn't catch that I'm missing the API call on line 500 of routes/api.py.
     Can you analyze that specific line?
```

### Agent Reporting False Positives

**Possible causes:**
1. Agent doesn't understand custom patterns in your code
2. Validation rules too strict for this use case

**Solution:**
```
You: The agent flagged line 300 as missing an API call, but this is an
     internal operation that shouldn't sync to Crossmark. Can you re-evaluate?
```

### Want More Detailed Analysis

**Solution:**
```
You: Can you run the sync validator in verbose mode with detailed
     analysis of the field mappings and data flow?
```

## Best Practices

### ✅ DO:
- Run validation after implementing any schedule/event/employee operations
- Review validation reports thoroughly before merging
- Address all ❌ Failed Checks before deployment
- Consider addressing ⚠️ Warnings for critical operations
- Use validation reports as code review checklist

### ❌ DON'T:
- Ignore validation warnings without understanding them
- Skip validation for "small changes" to sync code
- Override agent recommendations without documenting why
- Deploy code with Failed Checks
- Assume validation guarantees no bugs (it's a tool, not a guarantee)

## Getting Help

If you need assistance with validation reports:

```
You: I don't understand why the agent is saying my external_id handling is wrong.
     Can you explain the issue and show me the correct pattern?

Claude: Let me explain the validation finding...
        [provides detailed explanation with code examples]
```

## Advanced Usage

### Custom Validation Scenarios

```
You: Can you create a custom validation check that ensures all schedule
     deletions log the reason for deletion? Add this to the validator.

Claude: I'll update the external-api-sync-validator agent to include
        this custom check...
```

### Batch Validation

```
You: Please validate all files in routes/ directory that haven't been
     validated in the last week.

Claude: Running batch validation on routes/ directory...
        [generates report for each file]
```

### Integration Testing

```
You: After validation, please also run the integration tests for the
     External API to verify the changes work end-to-end.

Claude: Running validation followed by integration tests...
```

---

## Summary

The External API Sync Validator agent is a powerful tool for maintaining data integrity between your Flask application and the Crossmark API. Use it regularly, read the reports carefully, and address findings before deployment to prevent sync issues in production.

**Remember:** The agent is a safety net, not a replacement for understanding the sync logic yourself. Use it to catch mistakes and learn from the validation reports.
