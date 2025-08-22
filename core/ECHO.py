import inspect
import requests
from datetime import datetime
import threading
from time import sleep
import os
from unicodedata2 import normalize
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def build_start(PROCESSES_ID, SUB_PROCESS_ID, CLIENT_TOKEN):

    out_tk = ECHO()
    out_tk.PROCESSES_ID = PROCESSES_ID
    out_tk.SUB_PROCESS_ID = SUB_PROCESS_ID
    out_tk.CLIENT_TOKEN = CLIENT_TOKEN
    out_tk.INTERVAL_TIME_TO_UPDATE = 10
    out_tk.authenticate()
    out_tk.automationStart()
    return out_tk


class ECHO:
    CLIENT_TOKEN = ''
    SESSION_TOKEN = ''
    BASE_URL_API = 'https://portalecho.api.accenture.com'
    SUB_PROCESS_ID = ''
    ROB_LOG_USER_ID = os.environ.get('USERNAME')
    VERSION = '1.0'
    PROCESSES_ID = ''

    COUNT_TRANSACTIONS = 0  # Counter for the number of transactions already completed in the automation.
    LAST_DATATIME_UPDATE = datetime.now()  # It's used to track the last time an update was made
    INTERVAL_TIME_TO_UPDATE = 60 * 5 # Interval time to wait before sending the update to ECHO, in seconds.
    lock = threading.RLock()
    monitoring_active = False
    _monitoring_thread = None

    @classmethod
    def incrementTransaction(cls):
        """It's used to increment the transaction counter."""
        with cls.lock:
            cls.COUNT_TRANSACTIONS += 1

    @classmethod
    def getTransactionCounter(cls) -> int:
        """It's used to get the current transaction counter."""
        with cls.lock:
            return cls.COUNT_TRANSACTIONS

    @classmethod
    def setTransactionCounter(cls, value: int):
        """It's used to set the transaction counter to a specific value."""
        with cls.lock:
            cls.COUNT_TRANSACTIONS = value
            print(f"[ECHO] Transaction counter set to {cls.COUNT_TRANSACTIONS}", flush=True)

    @classmethod
    def resetTransactionCounter(cls):
        """It's used to reset the transaction counter."""
        with cls.lock:
            cls.COUNT_TRANSACTIONS = 0
            print(f"[ECHO] Transaction counter reset.", flush=True)

    @classmethod
    def updateLastDateTimeUpdate(cls):
        """It's used to update the last datetime of update."""
        with cls.lock:
            cls.LAST_DATATIME_UPDATE = datetime.now()
            print(f"[ECHO] Last update set to {cls.LAST_DATATIME_UPDATE.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    @classmethod
    def startMonitoring(cls, interval_time_to_update: int = None):
        """It's used to start monitoring the transaction counter and send updates to ECHO.
        :param interval_time_to_update: Interval time to wait before sending the update to ECHO, in seconds."""

        if interval_time_to_update is None:
            interval_time_to_update = cls.INTERVAL_TIME_TO_UPDATE

        def monitor():
            while True:
                sleep(1)
                with cls.lock:
                    if not cls.monitoring_active:
                        continue
                    tempo_passado = (datetime.now() - cls.LAST_DATATIME_UPDATE).total_seconds()
                    if tempo_passado >= interval_time_to_update:
                        print('*' * 20, flush=True)
                        print(f"[ECHO] Sending {cls.COUNT_TRANSACTIONS} transactions to the portal...", flush=True)
                        cls.automationUpdate(cls.COUNT_TRANSACTIONS)
                        print('*' * 20, flush=True)

        if not cls.monitoring_active:
            print(f"[ECHO] Starting monitoring with an interval of {interval_time_to_update} seconds.", flush=True)
            cls._monitoring_thread = threading.Thread(target=monitor, daemon=True)
            cls._monitoring_thread.start()
            cls.monitoring_active = True

    @classmethod
    def stopMonitoring(cls):
        """It's used to stop the monitoring thread."""

        if not cls.monitoring_active:
            print("[ECHO] Monitoring is already stopped.", flush=True)
            return

        print("[ECHO] Stopping monitoring...", flush=True)
        if cls._monitoring_thread:
            cls._monitoring_thread.join(timeout=5)
            cls.monitoring_active = False

    @classmethod
    def authenticate(cls, cont_tent: int = 0, max_tent: int = 0):
        """It's used to authenticate with the ECHO API and obtain a session token.
        :param cont_tent: Current attempt count.
        :param max_tent: Maximum number of attempts allowed."""

        try:
            print(f'Authenticating to the ECHO API. Attempt {cont_tent + 1} of {max_tent + 1}.', flush=True)
            payload = {"cliente_token": f"{cls.CLIENT_TOKEN}"}
            url_auth = f"{cls.BASE_URL_API}/api/authenticate"
            r = requests.post(url_auth, json=payload, verify=False)

            if 200 <= r.status_code < 300:
                cls.SESSION_TOKEN = r.json()['token']
                print(f'[ECHO] Authentication token successfully obtained: {cls.SESSION_TOKEN}', flush=True)
                return

            print(f'[ECHO] Error getting authentication token: {r.status_code} - {r.text}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.authenticate(cont_tent=cont_tent + 1)

            raise EchoExceptionGettingToken(status_code=r.status_code, status_text=r.text)

        except EchoExceptionGettingToken as e:
            print(f'[ECHO] Error getting authentication token:\n{e}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.authenticate(cont_tent=cont_tent + 1)
            raise e

        except Exception as e:
            print(f'Unknown error while authenticating on ECHO: {e}', flush=True)
            if (cont_tent < max_tent) and 'Erro ao obter token de autenticação' not in str(e):
                sleep(1)
                return cls.authenticate(cont_tent=cont_tent + 1)
            raise EchoExceptionUnknownError(method_name=inspect.currentframe().f_code.co_name, error=e)

    @classmethod
    def automationStart(cls, cont_tent: int = 0, max_tent: int = 0):
        """It's used to start the automation log in ECHO.
        :param cont_tent: Current attempt count.
        :param max_tent: Maximum number of attempts allowed."""

        try:
            if not cls.SESSION_TOKEN:
                if not cls.authenticate():
                    raise Exception('Authentication token is not set.')

            headers = {
                'Authorization': f"Bearer {cls.SESSION_TOKEN}",
                'Content-Type': 'application/json'
            }
            payload = {
                "sub_processo_id": f"{cls.SUB_PROCESS_ID}",
                "roboLog_processoVersao": f"{cls.VERSION}",
                "roboLog_userEID": f"{cls.ROB_LOG_USER_ID}"
            }

            url_start = f"{cls.BASE_URL_API}/api/automation/start"
            r = requests.post(url_start, headers=headers, json=payload, verify=False)
            if 200 <= r.status_code < 300:
                cls.startMonitoring()
                print('[ECHO] Automation started successfully.', flush=True)
                return

            print(f'[ECHO] Error while registering automation start execution log.'
                  f'\nStatus code: {r.status_code}\n'
                  f'Message: {r.text}, flush=True')
            if 'Token inválido e/ou expirado.' in r.text:
                raise Exception('Token de autenticação não está definido.')

            if cont_tent < max_tent:
                sleep(1)
                return cls.automationStart(cont_tent=cont_tent + 1)

            raise EchoExceptionStartingAutomation(status_code=r.status_code, status_text=r.text)

        except EchoExceptionStartingAutomation as e:
            print(f'[ECHO] Error while registering automation start execution log:\n{e}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.automationStart(cont_tent=cont_tent + 1)
            raise e

        except Exception as e:
            print(f'Unknown error while registering automation start execution log: {e}', flush=True)
            if (cont_tent < max_tent) and ('Erro ao registrar log de início de execução da automação' not in str(e)
                                           and 'Token de autenticação não está definido' not in str(e)) \
                    and 'Too many requests, please try again later' not in str(e):
                sleep(1)
                return cls.automationStart(cont_tent=cont_tent + 1)
            raise EchoExceptionUnknownError(method_name=inspect.currentframe().f_code.co_name, error=e)

    @classmethod
    def getVersion(cls, processo_id: str = None, versao_cod: str = None,
                   cont_tent: int = 0, max_tent: int = 0) -> dict:
        """It's used to validate the automation version on ECHO.
        :param processo_id: ID of the process in ECHO.
        :param versao_cod: Version code of the automation.
        :param cont_tent: Current attempt count.
        :param max_tent: Maximum number of attempts allowed."""

        if processo_id is None:
            processo_id = cls.PROCESSES_ID

        if versao_cod is None:
            versao_cod = cls.VERSION

        try:
            if not cls.SESSION_TOKEN:
                raise Exception('Authentication token is not set.')

            headers = {
                'Authorization': f"Bearer {cls.SESSION_TOKEN}",
                'Content-Type': 'application/json'
            }
            payload = {
                "processo_id": f"{processo_id}",
                "roboLog_processoVersao": f"{versao_cod}"
            }

            url_version = f"{cls.BASE_URL_API}/api/automation/v2/version"
            r = requests.post(url_version, headers=headers, json=payload, verify=False)
            if 200 <= r.status_code < 300:
                print('[ECHO] Versão obtida.', flush=True)
                return r.json()

            print(f'[ECHO] Error while getting automation version: {r.status_code} - {r.text}', flush=True)
            if 'Token inválido e/ou expirado.' in r.text:
                raise Exception('Authentication token is not set.')

            if cont_tent < max_tent:
                sleep(1)
                return cls.getVersion(processo_id=processo_id, versao_cod=versao_cod, cont_tent=cont_tent + 1)

            raise EchoExceptionGettingVersion(status_code=r.status_code, status_text=r.text)

        except EchoExceptionGettingVersion as e:
            print(f'[ECHO] Error while getting automation version:\n{e}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.getVersion(processo_id=processo_id, versao_cod=versao_cod, cont_tent=cont_tent + 1)
            raise e

        except Exception as e:
            print(f'Error while updating automation execution log{e}', flush=True)
            if (cont_tent < max_tent) and ('Token de autenticação não está definido' not in str(e)
                                           and 'Erro ao atualizar log de execução da automação' not in str(e)):
                sleep(1)
                return cls.getVersion(processo_id=processo_id, versao_cod=versao_cod, cont_tent=cont_tent + 1)
            raise EchoExceptionUnknownError(method_name=inspect.currentframe().f_code.co_name, error=e)

    @classmethod
    def automationUpdate(cls, num_transactions: int = None, cont_tent: int = 0, max_tent: int = 0):
        """It's used to update automation execution log.
        :param num_transactions: Number of transactions to update in the log.
        :param cont_tent: Current attempt count.
        :param max_tent: Maximum number of attempts allowed."""
        if num_transactions is None:
            num_transactions = cls.getTransactionCounter()

        try:
            with cls.lock:
                if not cls.SESSION_TOKEN:
                    raise Exception('Authentication token is not set.')

                headers = {
                    'Authorization': f"Bearer {cls.SESSION_TOKEN}",
                    'Content-Type': 'application/json'
                }
                payload = {
                    "sub_processo_id": f"{cls.SUB_PROCESS_ID}",
                    "transactions": f"{num_transactions}"
                }

                url_update = f"{cls.BASE_URL_API}/api/automation/update"
                print(f'[ECHO] Sending transactions: {num_transactions}...', flush=True)
                r = requests.put(url_update, headers=headers, json=payload, verify=False)
                if 200 <= r.status_code < 300:
                    cls.SESSION_TOKEN = r.json()['token'] if r.json()['token'] else cls.SESSION_TOKEN
                    cls.updateLastDateTimeUpdate()
                    cls.resetTransactionCounter()
                    print('[ECHO] Automation execution log updated successfully..', flush=True)
                    return

                print(
                    f'[ECHO] Error while updating automation execution log.\nStatus Code: '
                    f'{r.status_code}.\nMessage: {r.text}', flush=True)
                if 'Token inválido e/ou expirado.' in r.text:
                    raise Exception('Authentication token is not set.')

                if cont_tent < max_tent:
                    sleep(1)
                    return cls.automationUpdate(num_transactions=num_transactions, cont_tent=cont_tent + 1)

                raise EchoExceptionUpdatingAutomation(status_code=r.status_code, status_text=r.text)

        except EchoExceptionUpdatingAutomation as e:
            print(f'[ECHO] Error while updating automation execution log:\n{e}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.automationUpdate(num_transactions=num_transactions, cont_tent=cont_tent + 1)
            raise e

        except Exception as e:
            print(f'Unknown erro while updating automation execution log: {e}', flush=True)
            if (cont_tent < max_tent) and ('Token de autenticação não está definido' not in str(e)
                                           and 'Erro ao atualizar log de execução da automação' not in str(e)):
                sleep(1)
                return cls.automationUpdate(num_transactions=num_transactions, cont_tent=cont_tent + 1)
            raise EchoExceptionUnknownError(method_name=inspect.currentframe().f_code.co_name, error=e)

    @classmethod
    def automationFinish(cls, num_transactions: int = None, cont_tent: int = 0, max_tent: int = 0):
        """It's used to finish automation execution on ECHO.
        :param num_transactions: Number of transactions to finish in the log.
        :param cont_tent: Current attempt count.
        :param max_tent: Maximum number of attempts allowed."""

        if num_transactions is None:
            num_transactions = cls.getTransactionCounter()

        try:
            with cls.lock:
                if not cls.SESSION_TOKEN:
                    raise Exception('Authentication token is not set.')

                headers = {
                    'Authorization': f"Bearer {cls.SESSION_TOKEN}",
                    'Content-Type': 'application/json'
                }
                payload = {
                    "sub_processo_id": f"{cls.SUB_PROCESS_ID}",
                    "transactions": f"{num_transactions}"
                }

                url_finish = f"{cls.BASE_URL_API}/api/automation/finish"
                r = requests.put(url_finish, headers=headers, json=payload, verify=False)
                if 200 <= r.status_code < 300:
                    cls.stopMonitoring()
                    print('[ECHO] Automation finished successfully.', flush=True)
                    return

                print(f'[ECHO] Error while finishing automation execution log.'
                      f'\nStatus code {r.status_code}.\nMessage: {r.text}.', flush=True)
                if 'Token inválido e/ou expirado.' in r.text:
                    raise Exception('Authentication token is not set.')

                if cont_tent < max_tent:
                    sleep(1)
                    return cls.automationFinish(num_transactions=num_transactions, cont_tent=cont_tent + 1)

                raise EchoExceptionFinishingAutomation(status_code=r.status_code, status_text=r.text)

        except EchoExceptionFinishingAutomation as e:
            print(f'[ECHO] Error while finishing automation execution log:\n{e}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.automationFinish(num_transactions=num_transactions, cont_tent=cont_tent + 1)
            raise e

        except Exception as e:
            print(f'Unknown error while finishing automation execution log: {e}', flush=True)
            if (cont_tent < max_tent) and ('Token de autenticação não está definido' not in str(e) and
                                           'Erro ao finalizar log de execução da automação' not in str(e)):
                sleep(1)
                return cls.automationFinish(num_transactions=num_transactions, cont_tent=cont_tent + 1)
            raise EchoExceptionUnknownError(method_name=inspect.currentframe().f_code.co_name, error=e)

    @classmethod
    def automationError(cls, error_message: str, cont_tent: int = 0, max_tent: int = 0):
        """It's used to notify ECHO that a critical error occurred during execution. ECHO will stop the execution.
        :param error_message: Error message to be logged in ECHO.
        :param cont_tent: Current attempt count.
        :param max_tent: Maximum number of attempts allowed."""

        try:
            with cls.lock:
                if not cls.SESSION_TOKEN:
                    raise Exception('Authentication token is not set.')

                headers = {
                    'Authorization': f"Bearer {cls.SESSION_TOKEN}",
                    'Content-Type': 'application/json'
                }
                error_message = normalize('NFKD', error_message).encode('ASCII', 'ignore').decode('ASCII')
                payload = {
                    "sub_processo_id": f"{cls.SUB_PROCESS_ID}",
                    "error_message": f"{error_message}"
                }

                url_error = f"{cls.BASE_URL_API}/api/automation/error"
                r = requests.put(url_error, headers=headers, json=payload, verify=False)
                if 200 <= r.status_code < 300:
                    cls.stopMonitoring()
                    print('[ECHO] Automation error log successfully registered.', flush=True)
                    return

                print(
                    f'[ECHO] Error while registering automation error log.\nStatus Code: {r.status_code}.'
                    f'\nMessage: {r.text}.', flush=True)

                if 'Token inválido e/ou expirado.' in r.text:
                    raise Exception('Authentication token is not set.')

                if cont_tent < max_tent:
                    sleep(1)
                    return cls.automationError(error_message=error_message, cont_tent=cont_tent + 1)

                raise EchoExceptionUpdatingAutomationError(status_code=r.status_code, status_text=r.text)

        except EchoExceptionUpdatingAutomationError as e:
            print(f'[ECHO] Error while registering automation error log:\n{e}', flush=True)
            if cont_tent < max_tent:
                sleep(1)
                return cls.automationError(error_message=error_message, cont_tent=cont_tent + 1)
            raise e

        except Exception as e:
            print(f'Unknown error while registering automation error log{e}', flush=True)
            if (cont_tent < max_tent) and ('Token de autenticação não está definido' not in str(e) and
                                           'Erro ao registrar log de erro da automação' not in str(e)):
                sleep(1)
                return cls.automationError(error_message=error_message, cont_tent=cont_tent + 1)
            raise EchoExceptionUnknownError(method_name=inspect.currentframe().f_code.co_name, error=e)


class EchoExceptionGettingToken(Exception):
    """Custom exception for errors while getting the authentication token."""

    def __init__(self, status_code: int, status_text: str):
        message = (f'Error getting authentication token.\n'
                   f'Status Code: {status_code}.\n'
                   f'Message: {status_text}')
        super().__init__(message)


class EchoExceptionStartingAutomation(Exception):
    """Custom exception for errors while starting the automation."""

    def __init__(self, status_code: int, status_text: str):
        message = (f'Error starting automation.\n'
                   f'Status Code: {status_code}.\n'
                   f'Message: {status_text}')
        super().__init__(message)


class EchoExceptionGettingVersion(Exception):
    """Custom exception for errors while getting the automation version."""

    def __init__(self, status_code: int, status_text: str):
        message = (f'Error getting automation version.\n'
                   f'Status Code: {status_code}.\n'
                   f'Message: {status_text}')
        super().__init__(message)


class EchoExceptionUpdatingAutomation(Exception):
    """Custom exception for errors while updating the automation execution log."""

    def __init__(self, status_code: int, status_text: str):
        message = (f'Error updating automation execution log.\n'
                   f'Status Code: {status_code}.\n'
                   f'Message: {status_text}')
        super().__init__(message)


class EchoExceptionFinishingAutomation(Exception):
    """Custom exception for errors while finishing the automation execution log."""

    def __init__(self, status_code: int, status_text: str):
        message = (f'Error finishing automation execution log.\n'
                   f'Status Code: {status_code}.\n'
                   f'Message: {status_text}')
        super().__init__(message)


class EchoExceptionUpdatingAutomationError(Exception):
    """Custom exception for errors while getting the automation error log."""

    def __init__(self, status_code: int, status_text: str):
        message = (f'Error getting automation error log.\n'
                   f'Status Code: {status_code}.\n'
                   f'Message: {status_text}')
        super().__init__(message)


class EchoExceptionUnknownError(Exception):
    """Custom exception for unknown errors."""

    def __init__(self, method_name: str, error: Exception):
        message = (f"Unknown error in method: '{method_name}'.\n"
                   f"Error:\n{error}")
        super().__init__(message)