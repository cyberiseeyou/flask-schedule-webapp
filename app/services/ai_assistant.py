"""
AI Assistant Service

Natural language interface for scheduling operations using LLM function calling.
Supports both OpenAI and Anthropic Claude providers.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AssistantResponse:
    """Response from AI assistant"""
    response: str  # Natural language response
    data: Optional[Dict[str, Any]] = None  # Structured data
    actions: Optional[List[Dict[str, str]]] = None  # Suggested follow-up actions
    requires_confirmation: bool = False  # Whether action needs user confirmation
    confirmation_data: Optional[Dict[str, Any]] = None  # Data for confirmation
    tool_calls: Optional[List[Dict[str, Any]]] = None  # Raw tool calls made


class AIAssistant:
    """
    Natural language interface for scheduling operations

    Uses LLM function calling to map natural language queries to
    existing API endpoints and services.
    """

    def __init__(self, provider='openai', api_key=None, db_session=None, models=None):
        """
        Initialize AI Assistant

        Args:
            provider: LLM provider ('openai' or 'anthropic')
            api_key: API key for the provider
            db_session: SQLAlchemy database session
            models: Dictionary of database models
        """
        self.provider = provider
        self.api_key = api_key
        self.db = db_session
        self.models = models

        # Initialize LLM client
        self.client = self._init_client()

        # Import tools
        from app.services.ai_tools import AITools
        self.tools = AITools(db_session, models)

        # Get tool schemas
        self.tool_schemas = self.tools.get_tool_schemas()

    def _init_client(self):
        """Initialize LLM client based on provider"""
        if self.provider == 'openai':
            try:
                import openai
                return openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
        elif self.provider == 'anthropic':
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def process_query(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AssistantResponse:
        """
        Process natural language query

        Args:
            user_input: Natural language query from user
            conversation_history: Previous conversation messages

        Returns:
            AssistantResponse with natural language reply and data
        """
        try:
            # Build messages
            messages = self._build_messages(user_input, conversation_history)

            # Call LLM
            if self.provider == 'openai':
                response = self._call_openai(messages)
            elif self.provider == 'anthropic':
                response = self._call_anthropic(messages)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            return response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return AssistantResponse(
                response=f"I encountered an error: {str(e)}. Please try again.",
                data={'error': str(e)}
            )

    def _build_messages(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Build message list for LLM"""
        messages = []

        # System message
        system_message = self._get_system_prompt()
        messages.append({
            'role': 'system',
            'content': system_message
        })

        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user input
        messages.append({
            'role': 'user',
            'content': user_input
        })

        return messages

    def _get_system_prompt(self) -> str:
        """Get system prompt for AI assistant"""
        return """You are an AI assistant for a scheduling management system. Your role is to help managers with their daily scheduling tasks using natural language.

You have access to various tools that can:
- Query schedules and employee information
- Verify schedules for issues
- Generate paperwork
- Create time-off requests
- Manage event scheduling

When users ask questions:
1. Parse their intent and extract key information (dates, names, etc.)
2. Call the appropriate tool(s) with the correct parameters
3. Provide clear, concise responses
4. For write operations (scheduling, time-off, etc.), clearly state what action will be taken and mark it as requiring confirmation

Date handling:
- "tomorrow" = next day from today
- "Wednesday" = next Wednesday
- "this Friday" = upcoming Friday this week
- "next Monday" = Monday of next week
- Always use YYYY-MM-DD format internally

Employee names:
- Use fuzzy matching for employee names (e.g., "Diane" could match "Diane Martinez")
- If ambiguous, list options and ask for clarification

Be friendly, professional, and proactive. Suggest related actions when appropriate."""

    def _call_openai(self, messages: List[Dict[str, str]]) -> AssistantResponse:
        """Call OpenAI API with function calling"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=self.tool_schemas,
                tool_choice="auto",
                temperature=0.1  # Low temperature for consistent function calling
            )

            message = response.choices[0].message

            # Check if tool calls were made
            if message.tool_calls:
                return self._handle_tool_calls(message.tool_calls, messages)
            else:
                # No tool calls, just return the response
                return AssistantResponse(
                    response=message.content or "I'm not sure how to help with that.",
                    data=None
                )

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise

    def _call_anthropic(self, messages: List[Dict[str, str]]) -> AssistantResponse:
        """Call Anthropic Claude API with tool use"""
        try:
            # Anthropic expects system message separately
            system_message = messages[0]['content']
            conversation_messages = messages[1:]

            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                system=system_message,
                messages=conversation_messages,
                tools=self.tool_schemas,
                temperature=0.1
            )

            # Check for tool use
            tool_use_blocks = [block for block in response.content if block.type == 'tool_use']

            if tool_use_blocks:
                return self._handle_anthropic_tool_use(tool_use_blocks, messages)
            else:
                # Text response
                text_blocks = [block.text for block in response.content if hasattr(block, 'text')]
                return AssistantResponse(
                    response=' '.join(text_blocks) or "I'm not sure how to help with that.",
                    data=None
                )

        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}", exc_info=True)
            raise

    def _handle_tool_calls(
        self,
        tool_calls: List[Any],
        messages: List[Dict[str, str]]
    ) -> AssistantResponse:
        """Execute tool calls and format response (OpenAI format)"""
        results = []
        all_data = {}
        requires_confirmation = False
        confirmation_data = None

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            logger.info(f"Executing tool: {function_name} with args: {function_args}")

            # Execute the tool
            result = self.tools.execute_tool(function_name, function_args)
            results.append(result)

            # Merge data
            if result.get('data'):
                all_data.update(result['data'])

            # Check if confirmation is needed
            if result.get('requires_confirmation'):
                requires_confirmation = True
                confirmation_data = result.get('confirmation_data')

        # Generate natural language response
        final_response = self._format_tool_results(results)

        # Extract suggested actions
        actions = self._extract_actions(results)

        return AssistantResponse(
            response=final_response,
            data=all_data,
            actions=actions,
            requires_confirmation=requires_confirmation,
            confirmation_data=confirmation_data,
            tool_calls=[{
                'name': tc.function.name,
                'args': json.loads(tc.function.arguments)
            } for tc in tool_calls]
        )

    def _handle_anthropic_tool_use(
        self,
        tool_use_blocks: List[Any],
        messages: List[Dict[str, str]]
    ) -> AssistantResponse:
        """Execute tool use blocks and format response (Anthropic format)"""
        results = []
        all_data = {}
        requires_confirmation = False
        confirmation_data = None

        for tool_use in tool_use_blocks:
            function_name = tool_use.name
            function_args = tool_use.input

            logger.info(f"Executing tool: {function_name} with args: {function_args}")

            # Execute the tool
            result = self.tools.execute_tool(function_name, function_args)
            results.append(result)

            # Merge data
            if result.get('data'):
                all_data.update(result['data'])

            # Check if confirmation is needed
            if result.get('requires_confirmation'):
                requires_confirmation = True
                confirmation_data = result.get('confirmation_data')

        # Generate natural language response
        final_response = self._format_tool_results(results)

        # Extract suggested actions
        actions = self._extract_actions(results)

        return AssistantResponse(
            response=final_response,
            data=all_data,
            actions=actions,
            requires_confirmation=requires_confirmation,
            confirmation_data=confirmation_data,
            tool_calls=[{
                'name': tu.name,
                'args': tu.input
            } for tu in tool_use_blocks]
        )

    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """Format tool execution results into natural language"""
        if not results:
            return "I couldn't complete that request."

        # Collect all response messages
        messages = []
        for result in results:
            if result.get('success'):
                messages.append(result.get('message', ''))

        if not messages:
            return "I encountered an issue completing that request."

        return ' '.join(messages)

    def _extract_actions(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract suggested follow-up actions from tool results"""
        actions = []

        for result in results:
            if result.get('suggested_actions'):
                actions.extend(result['suggested_actions'])

        return actions if actions else None

    def confirm_action(self, confirmation_data: Dict[str, Any]) -> AssistantResponse:
        """
        Execute a confirmed action

        Args:
            confirmation_data: Data from the original requires_confirmation response

        Returns:
            AssistantResponse with execution results
        """
        try:
            tool_name = confirmation_data.get('tool_name')
            tool_args = confirmation_data.get('tool_args')

            if not tool_name or not tool_args:
                return AssistantResponse(
                    response="Invalid confirmation data.",
                    data={'error': 'Missing tool information'}
                )

            # Execute the tool with confirmed=True flag
            tool_args['_confirmed'] = True
            result = self.tools.execute_tool(tool_name, tool_args)

            return AssistantResponse(
                response=result.get('message', 'Action completed.'),
                data=result.get('data'),
                actions=result.get('suggested_actions')
            )

        except Exception as e:
            logger.error(f"Error confirming action: {str(e)}", exc_info=True)
            return AssistantResponse(
                response=f"Error executing action: {str(e)}",
                data={'error': str(e)}
            )
