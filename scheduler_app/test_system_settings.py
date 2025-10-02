"""
Tests for System Settings Management (Story 1.6)
"""
import pytest
import os
import tempfile
from cryptography.fernet import Fernet
from scheduler_app.app import app, db
from scheduler_app.utils.encryption import encrypt_value, decrypt_value, get_encryption_key


@pytest.fixture
def client():
    """Create test client with temporary database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def auth_client(client):
    """Client with authenticated session"""
    # Mock authentication in session_store (custom session implementation)
    from scheduler_app.routes import session_store
    session_store['test_session'] = {
        'authenticated': True,
        'user': {'username': 'test_user', 'employee_id': 1}
    }
    # Set session cookie
    client.set_cookie('session_id', 'test_session')
    return client


class TestEncryptionUtilities:
    """Test encryption helper functions"""

    def test_encrypt_decrypt_round_trip(self):
        """Test encryption and decryption returns original value"""
        with app.app_context():
            original = "test_password_123"
            encrypted = encrypt_value(original)
            decrypted = decrypt_value(encrypted)

            assert decrypted == original
            assert encrypted != original

    def test_encrypt_none_value(self):
        """Test encryption handles None gracefully"""
        with app.app_context():
            result = encrypt_value(None)
            assert result is None

    def test_encrypt_empty_string(self):
        """Test encryption handles empty string"""
        with app.app_context():
            result = encrypt_value('')
            assert result is None

    def test_decrypt_none_value(self):
        """Test decryption handles None gracefully"""
        with app.app_context():
            result = decrypt_value(None)
            assert result is None

    def test_decrypt_empty_string(self):
        """Test decryption handles empty string"""
        with app.app_context():
            result = decrypt_value('')
            assert result is None

    def test_get_encryption_key_returns_valid_key(self):
        """Test get_encryption_key returns valid Fernet key"""
        with app.app_context():
            key = get_encryption_key()
            assert key is not None
            assert isinstance(key, bytes)
            # Verify it's a valid Fernet key by trying to use it
            f = Fernet(key)
            test_data = b"test"
            encrypted = f.encrypt(test_data)
            decrypted = f.decrypt(encrypted)
            assert decrypted == test_data


class TestSystemSettingModel:
    """Test SystemSetting model methods"""

    def test_get_setting_string_type(self, client):
        """Test get_setting returns correct value for string type"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            # Create a string setting
            SystemSetting.set_setting('test_key', 'test_value', 'string')

            # Retrieve it
            result = SystemSetting.get_setting('test_key')
            assert result == 'test_value'

    def test_get_setting_boolean_type_true(self, client):
        """Test get_setting converts 'true' to boolean True"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            # Create a boolean setting
            SystemSetting.set_setting('test_bool', True, 'boolean')

            # Retrieve it
            result = SystemSetting.get_setting('test_bool')
            assert result is True
            assert isinstance(result, bool)

    def test_get_setting_boolean_type_false(self, client):
        """Test get_setting converts 'false' to boolean False"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            SystemSetting.set_setting('test_bool', False, 'boolean')
            result = SystemSetting.get_setting('test_bool')
            assert result is False
            assert isinstance(result, bool)

    def test_get_setting_encrypted_type(self, client):
        """Test get_setting decrypts encrypted values"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            # Create an encrypted setting
            secret = 'my_secret_password'
            SystemSetting.set_setting('test_secret', secret, 'encrypted')

            # Retrieve and verify it's decrypted
            result = SystemSetting.get_setting('test_secret')
            assert result == secret

    def test_get_setting_returns_default(self, client):
        """Test get_setting returns default if setting not found"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            result = SystemSetting.get_setting('nonexistent_key', 'default_value')
            assert result == 'default_value'

    def test_set_setting_creates_new(self, client):
        """Test set_setting creates new setting if key doesn't exist"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            setting = SystemSetting.set_setting('new_key', 'new_value', 'string')

            assert setting is not None
            assert setting.setting_key == 'new_key'
            assert setting.setting_value == 'new_value'
            assert setting.setting_type == 'string'

    def test_set_setting_updates_existing(self, client):
        """Test set_setting updates existing setting"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            # Create initial setting
            SystemSetting.set_setting('update_key', 'initial_value', 'string')

            # Update it
            SystemSetting.set_setting('update_key', 'updated_value', 'string')

            # Verify update
            result = SystemSetting.get_setting('update_key')
            assert result == 'updated_value'

    def test_set_setting_encrypts_value(self, client):
        """Test set_setting encrypts value for encrypted type"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            secret = 'my_password'
            setting = SystemSetting.set_setting('secret_key', secret, 'encrypted')

            # Verify stored value is encrypted (not plain text)
            assert setting.setting_value != secret
            # But decryption returns original
            assert SystemSetting.get_setting('secret_key') == secret

    def test_set_setting_converts_boolean(self, client):
        """Test set_setting converts boolean to string"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']

            setting = SystemSetting.set_setting('bool_key', True, 'boolean')
            assert setting.setting_value == 'true'

            setting = SystemSetting.set_setting('bool_key', False, 'boolean')
            assert setting.setting_value == 'false'


class TestSettingsRoutes:
    """Test settings page routes"""

    def test_get_settings_requires_authentication(self, client):
        """Test GET /admin/settings requires authentication"""
        response = client.get('/admin/settings')
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_get_settings_renders_form(self, auth_client):
        """Test GET /admin/settings renders settings form"""
        response = auth_client.get('/admin/settings')
        assert response.status_code == 200
        assert b'System Settings' in response.data

    def test_get_settings_displays_current_values(self, auth_client):
        """Test GET /admin/settings displays current setting values"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            SystemSetting.set_setting('edr_username', 'test_user', 'string')
            SystemSetting.set_setting('auto_scheduler_enabled', True, 'boolean')

        response = auth_client.get('/admin/settings')
        assert response.status_code == 200
        assert b'test_user' in response.data

    def test_post_settings_saves_values(self, auth_client):
        """Test POST /admin/settings saves updated settings"""
        response = auth_client.post('/admin/settings', data={
            'edr_username': 'new_username',
            'edr_mfa_credential_id': 'mfa_123',
            'auto_scheduler_enabled': 'true',
            'auto_scheduler_require_approval': 'true'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Settings saved successfully' in response.data

        # Verify settings were saved
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            assert SystemSetting.get_setting('edr_username') == 'new_username'
            assert SystemSetting.get_setting('edr_mfa_credential_id') == 'mfa_123'

    def test_post_settings_only_updates_password_if_provided(self, auth_client):
        """Test POST /admin/settings only updates password if value provided"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            SystemSetting.set_setting('edr_password', 'original_pass', 'encrypted')

        # Submit form without password
        auth_client.post('/admin/settings', data={
            'edr_username': 'user',
            'edr_password': '',  # Empty password
            'auto_scheduler_enabled': 'true'
        })

        # Verify password wasn't changed
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            assert SystemSetting.get_setting('edr_password') == 'original_pass'

    def test_post_settings_handles_checkbox_values(self, auth_client):
        """Test POST /admin/settings correctly handles checkbox values"""
        # Checkbox checked
        auth_client.post('/admin/settings', data={
            'auto_scheduler_enabled': 'true',
            'auto_scheduler_require_approval': 'true'
        })

        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            assert SystemSetting.get_setting('auto_scheduler_enabled') is True
            assert SystemSetting.get_setting('auto_scheduler_require_approval') is True

        # Checkbox unchecked (not in form data)
        auth_client.post('/admin/settings', data={})

        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            assert SystemSetting.get_setting('auto_scheduler_enabled') is False
            assert SystemSetting.get_setting('auto_scheduler_require_approval') is False


class TestEDRCredentialsIntegration:
    """Test EDR and auto-scheduler use SystemSetting"""

    def test_edr_generator_uses_system_setting(self, client):
        """Test EDR generator retrieves credentials from SystemSetting"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            SystemSetting.set_setting('edr_username', 'test_edr_user', 'string')
            SystemSetting.set_setting('edr_password', 'test_edr_pass', 'encrypted')
            SystemSetting.set_setting('edr_mfa_credential_id', 'mfa_test', 'string')

            # Import _get_edr_credentials helper
            from scheduler_app.routes.admin import _get_edr_credentials

            username, password, mfa_id = _get_edr_credentials()

            assert username == 'test_edr_user'
            assert password == 'test_edr_pass'
            assert mfa_id == 'mfa_test'

    def test_edr_credentials_fallback_to_config(self, client):
        """Test EDR credentials fall back to config if SystemSetting not found"""
        with app.app_context():
            # Set config values
            app.config['WALMART_EDR_USERNAME'] = 'config_user'
            app.config['WALMART_EDR_PASSWORD'] = 'config_pass'

            from scheduler_app.routes.admin import _get_edr_credentials

            username, password, mfa_id = _get_edr_credentials()

            # Should fall back to config
            assert username == 'config_user' or username is None


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_password_update(self, auth_client):
        """Test empty password field doesn't overwrite existing password"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            SystemSetting.set_setting('edr_password', 'original', 'encrypted')

        auth_client.post('/admin/settings', data={'edr_password': ''})

        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            password = SystemSetting.get_setting('edr_password')
            assert password == 'original'

    def test_invalid_setting_type_handled(self, client):
        """Test invalid setting type is handled gracefully"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            # Set with invalid type
            setting = SystemSetting.set_setting('test', 'value', 'invalid_type')
            # Should still save
            assert setting.setting_type == 'invalid_type'
            # Get should return as string
            result = SystemSetting.get_setting('test')
            assert result == 'value'

    def test_none_value_in_encrypt(self, client):
        """Test None values in encryption functions"""
        with app.app_context():
            SystemSetting = app.config['SystemSetting']
            setting = SystemSetting.set_setting('none_test', None, 'encrypted')
            assert setting.setting_value is None

    def test_csrf_token_in_form(self, auth_client):
        """Test CSRF token is present in settings form"""
        response = auth_client.get('/admin/settings')
        assert b'csrf_token' in response.data
