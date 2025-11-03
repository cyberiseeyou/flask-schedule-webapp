"""
AI Assistant API Routes

Handles natural language queries and AI assistant interactions
"""
from flask import Blueprint, request, jsonify, current_app, session
from app.routes.auth import require_authentication
from datetime import datetime
import logging

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
logger = logging.getLogger(__name__)


@ai_bp.route('/query', methods=['POST'])
@require_authentication()
def process_query():
    """
    Process natural language query

    Request Body:
        {
            "query": "Verify tomorrow's schedule",
            "conversation_id": "optional-session-id",
            "history": [...]  // Optional conversation history
        }

    Returns:
        {
            "response": "Natural language response",
            "data": {...},
            "actions": [...],
            "requires_confirmation": bool,
            "confirmation_data": {...},
            "conversation_id": "session-id"
        }
    """
    try:
        data = request.get_json()
        query = data.get('query')
        conversation_id = data.get('conversation_id')
        history = data.get('history', [])

        if not query:
            return jsonify({'error': 'Missing query parameter'}), 400

        # Get AI provider settings from config/environment
        provider = current_app.config.get('AI_PROVIDER', 'openai')
        api_key = current_app.config.get('AI_API_KEY')

        if not api_key:
            return jsonify({
                'error': 'AI assistant not configured. Please set AI_API_KEY in environment.'
            }), 503

        # Get database session and models
        from app.utils.db_helpers import get_models
        models = get_models()
        db = models['db']

        # Initialize AI assistant
        from app.services.ai_assistant import AIAssistant
        assistant = AIAssistant(
            provider=provider,
            api_key=api_key,
            db_session=db.session,
            models=models
        )

        # Process query
        result = assistant.process_query(query, history)

        # Store conversation in session if needed
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().timestamp()}"

        # Build response
        response = {
            'response': result.response,
            'data': result.data,
            'actions': result.actions,
            'requires_confirmation': result.requires_confirmation,
            'confirmation_data': result.confirmation_data,
            'conversation_id': conversation_id
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error processing AI query: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to process query',
            'details': str(e)
        }), 500


@ai_bp.route('/confirm', methods=['POST'])
@require_authentication()
def confirm_action():
    """
    Confirm and execute a pending action

    Request Body:
        {
            "confirmation_data": {...}
        }

    Returns:
        {
            "response": "Natural language response",
            "data": {...},
            "actions": [...]
        }
    """
    try:
        data = request.get_json()
        confirmation_data = data.get('confirmation_data')

        if not confirmation_data:
            return jsonify({'error': 'Missing confirmation_data'}), 400

        # Get AI provider settings
        provider = current_app.config.get('AI_PROVIDER', 'openai')
        api_key = current_app.config.get('AI_API_KEY')

        if not api_key:
            return jsonify({
                'error': 'AI assistant not configured'
            }), 503

        # Get database session and models
        from app.utils.db_helpers import get_models
        models = get_models()
        db = models['db']

        # Initialize AI assistant
        from app.services.ai_assistant import AIAssistant
        assistant = AIAssistant(
            provider=provider,
            api_key=api_key,
            db_session=db.session,
            models=models
        )

        # Execute confirmed action
        result = assistant.confirm_action(confirmation_data)

        response = {
            'response': result.response,
            'data': result.data,
            'actions': result.actions
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error confirming action: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to confirm action',
            'details': str(e)
        }), 500


@ai_bp.route('/suggestions', methods=['GET'])
@require_authentication()
def get_suggestions():
    """
    Get suggested queries/actions for the user

    Returns:
        {
            "suggestions": [
                {"label": "Verify tomorrow's schedule", "query": "verify schedule for tomorrow"},
                ...
            ]
        }
    """
    from datetime import date, timedelta

    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%A')

    suggestions = [
        {
            'label': f'Verify {tomorrow_str}\'s schedule',
            'query': 'verify schedule for tomorrow',
            'icon': '🔍'
        },
        {
            'label': f'How many employees on {tomorrow_str}?',
            'query': 'how many employees tomorrow',
            'icon': '👥'
        },
        {
            'label': 'Show unscheduled events',
            'query': 'list unscheduled events',
            'icon': '📌'
        },
        {
            'label': f'Print {tomorrow_str}\'s paperwork',
            'query': 'print paperwork for tomorrow',
            'icon': '🖨️'
        },
        {
            'label': 'Check time-off requests',
            'query': 'check time off requests',
            'icon': '📋'
        },
        {
            'label': 'View this week\'s schedule',
            'query': 'show schedule summary for this week',
            'icon': '📅'
        }
    ]

    return jsonify({'suggestions': suggestions}), 200


@ai_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check if AI assistant is properly configured

    Returns:
        {
            "status": "ok" | "error",
            "provider": "openai" | "anthropic",
            "configured": bool
        }
    """
    provider = current_app.config.get('AI_PROVIDER', 'openai')
    api_key = current_app.config.get('AI_API_KEY')

    return jsonify({
        'status': 'ok' if api_key else 'error',
        'provider': provider,
        'configured': bool(api_key),
        'message': 'AI assistant ready' if api_key else 'AI_API_KEY not configured'
    }), 200
