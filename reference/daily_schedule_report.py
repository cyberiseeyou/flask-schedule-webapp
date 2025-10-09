import requests
import json


def get_daily_schedule_report(auth_token, cookies=None):
    """
    Get daily schedule report from Walmart Retail Link Event Management

    Args:
        auth_token: Bearer token for authorization
        cookies: Optional cookies dict (can be extracted from session)

    Returns:
        dict: JSON response with daily schedule report
    """
    DAILY_REPORT_URL = "https://retaillink2.wal-mart.com/EventManagement/api/store-event/daily-schedule-report"

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {auth_token}",
        "content-type": "application/json",
        "origin": "https://retaillink2.wal-mart.com",
        "priority": "u=1, i",
        "referer": "https://retaillink2.wal-mart.com/EventManagement/daily-scheduled-report",
        "sec-ch-ua": '"Microsoft Edge";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0",
    }

    payload = {
        "startDate": "2025-09-01",
        "endDate": "2025-10-04",
        "eventType": [
            1,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
        ],
        "clubList": [8135],
        "walmartWeekYear": "",
    }

    # If using a session with cookies
    if cookies:
        response = requests.post(
            DAILY_REPORT_URL, headers=headers, json=payload, cookies=cookies
        )
    else:
        response = requests.post(DAILY_REPORT_URL, headers=headers, json=payload)

    response.raise_for_status()
    return response.json()


# Example usage with session (recommended if you're already authenticated):
def get_daily_schedule_with_session(
    session, auth_token, start_date, end_date, club_numbers
):
    """
    Get daily schedule report using existing session

    Args:
        session: requests.Session object with cookies already set
        auth_token: Bearer token
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        club_numbers: List of club/store numbers
    """
    url = "https://retaillink2.wal-mart.com/EventManagement/api/store-event/daily-schedule-report"

    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {auth_token}",
        "content-type": "application/json",
        "referer": "https://retaillink2.wal-mart.com/EventManagement/daily-scheduled-report",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    }

    payload = {
        "startDate": start_date,
        "endDate": end_date,
        "eventType": list(range(1, 58)),  # All event types 1-57
        "clubList": club_numbers,
        "walmartWeekYear": "",
    }

    response = session.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
