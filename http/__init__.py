import requests
import uuid

from flask import Blueprint, current_app, jsonify, request
from flask_api import status


name = 'HTTP'
prefix = 'http'
storage_enabled = False

plugin = Blueprint(name, __name__)


def register(app, plugin_storage_path=None):
    app.register_blueprint(plugin, url_prefix=f'/{prefix}')
    app.logger.info(f'{name} plugin registered.')


persistence = {
    "configuration": {},
    "execution": {},
}


@plugin.route('/')
def index():
    return f'This is the Radon CTT Agent HTTP Plugin.', status.HTTP_200_OK


@plugin.route('/configuration/', methods=['POST'])
def configuration_create():
    config_instance = {}
    configuration_uuid = str(uuid.uuid4())
    config_instance['uuid'] = configuration_uuid

    params = {
        'use_https': {
            'required': True,
            'default': False,
        },
        'method': {
            'required': True,
            'default': 'GET',
        },
        'hostname': {
            'required': True,
            'default': None,
        },
        'port': {
            'required': True,
            'default': 80,
        },
        'path': {
            'required': True,
            'default': "/",
        },
        'test_body': {
            'required': False,
            'default': None,
        },
        'test_header': {
            'required': False,
            'default': None,
        },
        'expected_status': {
            'required': True,
            'default': 200,
        },
        'expected_body': {
            'required': False,
            'default': None,
        },
    }

    for param in params:
        is_required = params[param]['required']
        default_value = params[param]['default']

        if param in request.form:
            value = request.form.get(param, type=str)
            current_app.logger.info(f'\'{param}\' set to: \'{value}\'.')
            config_instance[param] = value
        else:
            if is_required and default_value is not None:
                value = default_value
                current_app.logger.info(f'\'{param}\' set to default value: \'{value}\'.')
                config_instance[param] = value

        if is_required and param not in config_instance:
            return f'Required parameter {param} not provided.', status.HTTP_400_BAD_REQUEST

    persistence['configuration'][configuration_uuid] = config_instance
    return jsonify(config_instance), status.HTTP_201_CREATED


@plugin.route('/execution/', methods=['POST'])
def execution():
    execution_instance = {}

    if 'config_uuid' in request.form:
        config_uuid = request.form['config_uuid']
        config_entry = persistence['configuration'][config_uuid]
        execution_instance['config'] = config_entry

        # Assign values from config if they are stored in the config, otherwise assign None
        use_https = bool(config_entry['use_https']) if 'use_https' in config_entry else None
        method = str(config_entry['method']).upper() if 'method' in config_entry else None
        hostname = str(config_entry['hostname']) if 'hostname' in config_entry else None
        port = int(config_entry['port']) if 'port' in config_entry else None
        path = str(config_entry['path']) if 'path' in config_entry else None
        test_body = config_entry['test_body'] if 'test_body' in config_entry else None
        test_header = config_entry['test_header'] if 'test_header' in config_entry else None
        expected_status = int(config_entry['expected_status']) if 'expected_status' in config_entry else None
        expected_body = config_entry['expected_body'] if 'expected_body' in config_entry else None

        # Check if required parameters are set
        if use_https is not None and method and hostname and port and path and expected_status:

            protocol = 'http'
            if use_https:
                protocol += 's'

            target_url = f'{protocol}://{hostname}:{port}{path}'

            # Send request with given parameters
            response = requests.request(method, target_url, headers=test_header, json=test_body)

            response_status = response.status_code

            # Create UUID for execution
            execution_uuid = str(uuid.uuid4())
            execution_instance['uuid'] = execution_uuid
            execution_instance['target_url'] = target_url
            execution_instance['expected_status'] = str(expected_status)
            execution_instance['actual_status'] = str(response_status)

            if response_status == expected_status:
                if expected_body:
                    response_body = response.json()
                    execution_instance['expected_body'] = str(expected_body)
                    execution_instance['actual_body'] = str(response_body)
                    if expected_body == response_body:
                        execution_instance['success'] = True
                    else:
                        execution_instance['success'] = False
                else:
                    execution_instance['success'] = True
            else:
                execution_instance['success'] = False

            persistence['execution'][execution_uuid] = execution_instance

            # Test was executed with any possible outcome
            return jsonify(execution_instance), status.HTTP_200_OK

        else:
            return "Required configuration parameters are missing.", jsonify(config_entry), status.HTTP_400_BAD_REQUEST
    else:
        return "No configuration with that ID found.", jsonify(persistence), status.HTTP_404_NOT_FOUND
