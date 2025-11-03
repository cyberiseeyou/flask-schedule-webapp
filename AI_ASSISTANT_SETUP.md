# 🤖 AI Assistant Setup Guide

## Overview

The AI Assistant is a natural language interface for the scheduling system that allows managers to interact with the application using conversational queries. It supports **OpenAI GPT-4o-mini**, **Anthropic Claude 3.5 Haiku**, and **Google Gemini 1.5 Flash**.

---

## Features

### 🔍 Read Operations (Query Tools)
1. **verify_schedule** - Verify schedules for any date and identify issues
2. **count_employees** - Count employees working on a specific date
3. **get_schedule** - Get detailed schedule information
4. **check_time_off** - Check time-off requests
5. **get_unscheduled_events** - List unscheduled events

### ✏️ Write Operations (Action Tools)
6. **print_paperwork** - Generate daily paperwork PDFs
7. **request_time_off** - Create time-off requests for employees
8. **get_employee_info** - Get employee details
9. **list_employees** - List all active employees
10. **get_schedule_summary** - Get schedule summary for date ranges

All write operations require user confirmation before execution for safety.

---

## Installation

### 1. Install Required Packages

Add AI packages to your requirements:

```bash
# For Google Gemini (Recommended - CHEAPEST!)
pip install google-generativeai

# OR for OpenAI (Fast & Affordable)
pip install openai

# OR for Anthropic Claude
pip install anthropic

# All can be installed if you want flexibility
pip install google-generativeai openai anthropic
```

### 2. Get API Keys

#### Option A: Google Gemini (Recommended - CHEAPEST!)
1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Cost: **~$0.075 per 1M tokens (~$0.11/month for 50 queries/day)** ⭐ BEST VALUE!

#### Option B: OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Cost: ~$0.15 per 1M tokens (~$0.23/month for 50 queries/day)

#### Option C: Anthropic Claude
1. Go to https://console.anthropic.com/
2. Create an API key
3. Cost: ~$0.25 per 1M tokens (~$0.38/month for 50 queries/day)

### 3. Configure Environment Variables

Add to your `.env` file or environment:

```bash
# For Google Gemini (Recommended)
AI_PROVIDER=gemini
AI_API_KEY=your-gemini-api-key-here

# OR for OpenAI
AI_PROVIDER=openai
AI_API_KEY=sk-proj-your-openai-api-key-here

# OR for Anthropic
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-your-anthropic-api-key-here
```

**Security Note:** Never commit API keys to version control. Always use environment variables or a secrets manager.

---

## Configuration

### app/config.py

The AI assistant configuration is automatically loaded from environment variables:

```python
# AI Assistant Configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')  # 'gemini', 'openai', or 'anthropic'
AI_API_KEY = os.getenv('AI_API_KEY')
```

---

## Usage

### Accessing the AI Assistant

The AI Assistant is available on every page via:

1. **Floating Chat Bubble** - Click the 🤖 button in the bottom-right corner
2. **Keyboard Shortcut** - Press `Ctrl+K` (Windows/Linux) or `Cmd+K` (Mac)

### Example Queries

```
✅ "Verify tomorrow's schedule"
✅ "How many employees are working Wednesday?"
✅ "Print paperwork for tomorrow"
✅ "Add time off for Diane next Friday for a doctor appointment"
✅ "Who's working the 9:45 shift tomorrow?"
✅ "Show unscheduled events for this week"
✅ "Check time off requests"
✅ "List all Lead Event Specialists"
```

### Natural Language Date Parsing

The AI understands natural language dates:
- **"tomorrow"** - Next day
- **"Wednesday"** - Next Wednesday
- **"this Friday"** - Upcoming Friday this week
- **"next Monday"** - Monday of next week
- **"this week"** - Current week (Sun-Sat)
- **"2025-11-04"** - Specific date (YYYY-MM-DD)

### Fuzzy Employee Name Matching

The AI can match employee names even with partial input:
- **"Diane"** → Matches "Diane Martinez"
- **"Mike"** → Matches "Michael Williams"
- **"sarah j"** → Matches "Sarah Johnson"

---

## Architecture

### Component Structure

```
app/
├── services/
│   ├── ai_assistant.py          # Core AI service & LLM integration
│   └── ai_tools.py               # Tool definitions & implementations
├── routes/
│   └── ai_routes.py              # API endpoints (/api/ai/*)
├── static/js/components/
│   └── ai-assistant.js           # Frontend chat UI controller
└── templates/components/
    └── ai_chat_bubble.html       # Floating chat bubble component
```

### API Endpoints

#### POST /api/ai/query
Process natural language queries

**Request:**
```json
{
  "query": "Verify tomorrow's schedule",
  "conversation_id": "optional-session-id",
  "history": []
}
```

**Response:**
```json
{
  "response": "✅ All clear! Verified schedule for Thursday...",
  "data": {...},
  "actions": [
    {"label": "View Full Report", "action": "/schedule-verification?date=2025-11-04"}
  ],
  "requires_confirmation": false,
  "confirmation_data": null,
  "conversation_id": "conv_12345"
}
```

#### POST /api/ai/confirm
Confirm and execute a pending action

**Request:**
```json
{
  "confirmation_data": {
    "tool_name": "request_time_off",
    "tool_args": {...}
  }
}
```

#### GET /api/ai/suggestions
Get suggested queries

#### GET /api/ai/health
Check AI configuration status

---

## Cost Analysis

### Monthly Cost Estimates

**Assumptions:**
- 50 queries per day
- 500 tokens average per query
- 30 days per month

| Provider | Model | Cost per 1M Tokens | Monthly Cost | Recommendation |
|----------|-------|-------------------|--------------|----------------|
| **Google** ⭐ | **Gemini 1.5 Flash** | **$0.15** | **$0.11/month** | **BEST VALUE** |
| OpenAI | GPT-4o-mini | $0.30 | $0.23/month | Fast & Reliable |
| Anthropic | Claude 3.5 Haiku | $0.50 | $0.38/month | High Quality |

**Annual cost: $1.32 - $4.56/year** (incredibly affordable!)

**🏆 Winner: Google Gemini 1.5 Flash - 50% cheaper than OpenAI, excellent function calling!**

---

## Security & Privacy

### Data Handling
- ✅ Function calling ensures only function names/parameters sent to LLM
- ✅ Sensitive employee data (SSN, passwords) never sent externally
- ✅ All write operations require explicit user confirmation
- ✅ Audit logging for all AI-initiated actions

### Best Practices
1. **Never hardcode API keys** - Use environment variables
2. **Monitor API usage** - Set up billing alerts on provider dashboards
3. **Rate limiting** - Consider adding rate limits for production
4. **Audit trail** - Review AI actions regularly

---

## Troubleshooting

### AI Assistant Not Appearing

1. Check browser console for JavaScript errors
2. Verify `ai_chat_bubble.html` is included in `base.html`
3. Ensure JavaScript file path is correct

### "AI assistant not configured" Error

1. Verify `AI_API_KEY` environment variable is set
2. Check `.env` file is loaded (restart Flask app)
3. Test API key with provider's dashboard

### LLM Not Responding

1. Check API key validity
2. Verify internet connection
3. Check provider status page (status.openai.com / status.anthropic.com)
4. Review Flask logs for error details

### Tool Execution Errors

1. Check database connection
2. Verify model imports in `get_models()`
3. Review tool method logs in Flask console

---

## Extending the AI Assistant

### Adding New Tools

1. **Define Tool Schema** in `ai_tools.py`:
```python
{
    "type": "function",
    "function": {
        "name": "your_tool_name",
        "description": "What this tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["param1"]
        }
    }
}
```

2. **Implement Tool Method**:
```python
def _tool_your_tool_name(self, args: Dict[str, Any]) -> Dict[str, Any]:
    """Your tool implementation"""
    # Your logic here
    return {
        'success': True,
        'message': 'Natural language response',
        'data': {...}
    }
```

3. **Register in Tool Map**:
```python
tool_map = {
    # ...
    'your_tool_name': self._tool_your_tool_name,
}
```

### Adding Confirmation Requirements

For write operations, return:
```python
return {
    'success': True,
    'message': '⚠️ Confirm: [Action description]?',
    'requires_confirmation': True,
    'confirmation_data': {
        'tool_name': 'your_tool',
        'tool_args': args,
        'action': 'Human-readable action'
    }
}
```

---

## Development Roadmap

### Phase 1 ✅ (Complete)
- Core AI assistant service
- 10 tools (5 read, 5 write)
- Floating chat bubble UI
- OpenAI & Anthropic support

### Phase 2 🚧 (Future)
- Conversation memory/context
- Proactive suggestions
- Voice input support
- Multi-turn conversations

### Phase 3 📋 (Planned)
- Learning from corrections
- Custom training data
- Advanced scheduling AI
- Predictive analytics

---

## Testing

### Manual Testing

```bash
# Start Flask app
flask run

# Open browser to http://localhost:5000
# Click AI chat bubble (🤖)
# Try sample queries:
"Verify tomorrow's schedule"
"How many employees Wednesday?"
"Print paperwork for tomorrow"
```

### API Testing

```bash
curl -X POST http://localhost:5000/api/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query": "verify tomorrow schedule"}'
```

---

## Support & Resources

### Documentation
- OpenAI Docs: https://platform.openai.com/docs
- Anthropic Docs: https://docs.anthropic.com
- Function Calling Guide: https://platform.openai.com/docs/guides/function-calling

### Cost Monitoring
- OpenAI Usage: https://platform.openai.com/usage
- Anthropic Console: https://console.anthropic.com/

### Issues & Feedback
Report issues or suggestions via GitHub Issues or your internal ticketing system.

---

## License

This AI Assistant feature is part of the Product Connections Scheduler application and follows the same license terms as the main project.

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**

Co-Authored-By: Claude <noreply@anthropic.com>
