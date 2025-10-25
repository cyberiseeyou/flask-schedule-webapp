# Custom Agents for Flask Schedule Webapp

This directory contains specialized agents designed for this codebase.

## Available Agents

### external-api-sync-validator

**Purpose:** Validates External API integration and ensures synchronization between Crossmark API and local database.

**When to Use:**
- After making changes to routes that handle schedules, events, or employees
- When modifying database models with external_id tracking
- Before merging features that interact with Crossmark API
- During code review of sync-related changes
- When debugging data synchronization issues

**How to Invoke:**

The agent can be invoked manually or automatically as part of your development workflow.

#### Manual Invocation
```
Use the Task tool with the external-api-sync-validator agent to validate specific changes.
```

#### Automatic Invocation (Recommended)
Set up a git hook to automatically validate changes before commit:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Check if any sync-critical files were modified
if git diff --cached --name-only | grep -qE "(routes/api\.py|routes/scheduling\.py|models/schedule\.py|sync_engine\.py)"; then
    echo "🔍 Running External API Sync Validator..."
    # Invoke the agent here
    # (Implementation depends on your workflow automation)
fi
```

**Key Features:**
- Validates all External API integration touchpoints
- Checks for proper PHPSESSID authentication
- Verifies external_id field tracking
- Ensures correct field mappings (store_number, location_mvid, etc.)
- Detects missing API calls
- Validates error handling patterns
- Generates comprehensive validation reports

**Files Monitored:**
- `routes/api.py` - Schedule CRUD operations
- `routes/scheduling.py` - Manual scheduling
- `routes/auto_scheduler.py` - Bulk scheduling
- `models/schedule.py`, `models/event.py`, `models/employee.py` - Data models
- `session_api_service.py` - External API client
- `sync_engine.py` - Sync orchestration
- `services/sync_service.py` - Background sync tasks

**Example Report:**
See `EXAMPLE_VALIDATION_REPORT.md` for a complete validation report example based on the reissue event feature.

## Agent Development Guidelines

When creating new agents for this project:

1. **Follow the Agent Specification Format:**
   ```yaml
   ---
   name: agent-name
   description: When to use this agent
   tools: List of tools the agent can use
   ---
   ```

2. **Include Clear Invocation Criteria:**
   - Define exactly when the agent should be called
   - Specify file patterns or change types that trigger the agent
   - Provide examples of appropriate use cases

3. **Provide Validation Checklists:**
   - Create specific, actionable checks
   - Include code examples (good vs. bad patterns)
   - Define success criteria

4. **Generate Structured Reports:**
   - Use consistent formatting
   - Categorize findings: Passed, Warnings, Failed
   - Include specific file locations and line numbers
   - Provide remediation recommendations

5. **Document Anti-Patterns:**
   - List common mistakes to detect
   - Show incorrect vs. correct implementations
   - Explain the impact of each anti-pattern

## Integration with Development Workflow

### Pre-Commit Validation
```bash
# Recommended: Run validation before committing sync-related changes
git add routes/api.py
# Manually invoke agent to validate changes
# Review report
git commit -m "Add new schedule endpoint"
```

### Code Review Process
1. Developer creates PR with sync-related changes
2. Reviewer invokes external-api-sync-validator agent
3. Agent generates validation report
4. Reviewer uses report to guide code review
5. Developer addresses any warnings or failures
6. PR approved only after agent validation passes

### Continuous Integration
Consider integrating agent validation into CI/CD pipeline:
```yaml
# .github/workflows/validate-sync.yml
name: Validate External API Sync
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Sync Validator
        run: |
          # Invoke external-api-sync-validator agent
          # Parse validation report
          # Fail CI if critical issues found
```

## Agent Maintenance

### Updating Agents
When updating agent specifications:
1. Document changes in agent file comments
2. Update EXAMPLE reports if validation criteria change
3. Test agent with historical code changes to ensure accuracy
4. Notify team of agent behavior changes

### Adding New Validation Rules
To add new validation rules to external-api-sync-validator:
1. Identify new integration pattern or anti-pattern
2. Add to relevant validation phase in agent specification
3. Create example showing correct implementation
4. Update validation report template
5. Test with existing codebase

## Support

For questions about agents or to report issues:
1. Review agent specification in detail
2. Check EXAMPLE_VALIDATION_REPORT.md for expected output
3. Verify you're invoking the agent correctly
4. Document any unexpected behavior for agent improvement

## Future Agents

Potential agents to develop:
- **database-migration-validator**: Ensures migrations don't break external_id tracking
- **api-endpoint-security**: Validates authentication and authorization
- **performance-analyzer**: Checks for N+1 queries and slow operations
- **test-coverage-enforcer**: Ensures new endpoints have adequate tests
