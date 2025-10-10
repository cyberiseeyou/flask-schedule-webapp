# HIGH-03: Implement Circuit Breaker Pattern for External APIs

## Priority
🟡 **HIGH** - Within 2 Weeks

## Status
🟡 Open

## Type
🔨 Resilience / Error Handling

## Assigned To
**Dev Agent (James)**

## Description
External API calls (Crossmark, Walmart EDR) lack circuit breaker pattern, causing cascading failures when APIs are down. Application hangs waiting for timeouts.

## Current Issues
- No retry logic with exponential backoff
- No circuit breaker to prevent repeated failures
- Application blocks on failed API calls
- No fallback strategies

## Solution: Implement pybreaker

```python
# utils/circuit_breaker.py
from pybreaker import CircuitBreaker
import logging

logger = logging.getLogger(__name__)

# Crossmark API circuit breaker
crossmark_breaker = CircuitBreaker(
    fail_max=5,              # Open after 5 failures
    timeout_duration=60,     # Try again after 60 seconds
    expected_exception=RequestException,
    name='CrossmarkAPI'
)

# Walmart EDR circuit breaker
edr_breaker = CircuitBreaker(
    fail_max=3,
    timeout_duration=120,
    expected_exception=RequestException,
    name='WalmartEDR'
)

@crossmark_breaker
def call_crossmark_api(endpoint, data):
    """Call Crossmark API with circuit breaker protection"""
    try:
        response = requests.post(endpoint, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.error(f"Crossmark API error: {e}")
        raise
```

## Usage
```python
from utils.circuit_breaker import crossmark_breaker, call_crossmark_api

try:
    result = call_crossmark_api('/schedule', data)
except CircuitBreakerError:
    # Circuit is open - fail fast
    return jsonify({'error': 'External service temporarily unavailable'}), 503
```

## Acceptance Criteria
- [ ] Install pybreaker library
- [ ] Create circuit breaker wrappers for Crossmark API
- [ ] Create circuit breaker wrappers for Walmart EDR API
- [ ] Add retry logic with exponential backoff
- [ ] Add health check endpoints
- [ ] Implement fallback strategies
- [ ] Add circuit breaker status to admin dashboard
- [ ] Tests for circuit breaker behavior

## Estimated Effort
⏱️ **12-16 hours**

---
**Created**: 2025-01-09
