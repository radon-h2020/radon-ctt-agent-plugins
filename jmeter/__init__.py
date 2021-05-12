# Native imports
import datetime
import json
import os
import shutil
import tempfile
import uuid
import zipfile

# Module imports
from flask import Blueprint, current_app, jsonify, request, send_file

name = 'JMeter'
prefix = 'jmeter'
storage_enabled = True
global storage_path

plugin = Blueprint(name, __name__)


def register(app, plugin_storage_path=None):
    app.register_blueprint(plugin, url_prefix=f'/{prefix}')
    app.logger.info(f'{name} plugin registered.')
    global storage_path
    storage_path = plugin_storage_path


persistence = {
    "configuration": {},
    "execution": {},
}

jmeter_executable = '/usr/bin/env jmeter'
resources_filename = 'resources.zip'
test_properties_filename = "jmeter.properties"
test_run_log_filename = 'run.log'
test_results_dashboard_folder_name = 'dashboard'
test_sample_results_filename = 'sample_results.jtl'

# Folder in local storage where configuration artifacts are stored
# (e.g., <storage_path>/<config_uuid>/<storage_config_folder_name/)
storage_config_folder_name = 'config'

result_zip_file_name = 'results.zip'

# Names of the folders in the results zip file
result_config_folder_name = 'config'
result_execution_folder_name = 'execution'


@plugin.route('/')
def index():
    return f'This is the Radon CTT Agent JMeter Plugin.', 200


############# JMETER #############

# Create Configuration
@plugin.route('/configuration/', methods=['POST'])
def configuration_create():
    config_instance = {}

    configuration_uuid = str(uuid.uuid4())
    config_instance['uuid'] = configuration_uuid

    config_path_relative = os.path.join(configuration_uuid, storage_config_folder_name)
    config_path = os.path.join(storage_path, config_path_relative)
    os.makedirs(config_path, exist_ok=True)

    current_app.logger.debug(json.dumps(request.form))

    # Host (form)
    if 'host' in request.form:
        host = request.form.get('host', type=str)
        current_app.logger.info(f'\'host\' set to: {host}')
        config_instance['host'] = host

    # Port (form)
    if 'port' in request.form:
        port = request.form.get('port')
        current_app.logger.info(f'\'port\' set to: {port}')
        config_instance['port'] = port

    # Test resources (file) and JMX file name (form)
    if 'resources' in request.files and 'jmx_file_name' in request.form:

        # Get file from request
        resources_file = request.files['resources']
        resources_zip_path = os.path.join(config_path, resources_filename)
        resources_file.save(resources_zip_path)

        # Extract resources
        resources_extract_dir = os.path.join(config_path, 'resources')
        os.makedirs(resources_extract_dir)
        with zipfile.ZipFile(resources_zip_path, 'r') as res_zip:
            res_zip.extractall(resources_extract_dir)

        # Get name of the JMX file from request
        jmx_file_name = request.form.get('jmx_file_name')
        current_app.logger.info(f'\'jmx_file_name\' set to: {jmx_file_name}')
        config_instance['jmx_file_name'] = jmx_file_name

        # Check if JMX file with the given name exists in extracted directory
        # Test plan = JMX file inside the extracted resource zip with the name of 'jmx_file_name'
        test_plan_path = os.path.join(config_path, 'resources', jmx_file_name)
        if os.path.isfile(test_plan_path):
            test_plan_path_relative = os.path.relpath(test_plan_path, storage_path)
            config_instance['test_plan'] = test_plan_path_relative

            current_app.logger.debug(f'\'test_plan\' full path is: {test_plan_path}')
            current_app.logger.info(f'\'test_plan\' set to: {test_plan_path_relative}')
        else:
            current_app.logger.error(f'\'test_plan\' could not be found in {test_plan_path}.')
            raise FileNotFoundError(f'\'test_plan\' could not be found in {test_plan_path}.')
    else:
        if 'resources' not in request.files:
            error_str = f'\'resources\' could not be found in \'request.files\''
        elif 'jmx_file_name' not in request.form:
            error_str = f'\'jmx_file_name\' could not be found in \'request.form\''
        else:
            error_str = f'No test resources and/or JMX file name provided.', 400

        current_app.logger.error(error_str)
        raise FileNotFoundError(error_str)

    # Properties file
    if 'properties' in request.files:
        properties = request.files['properties']
        properties_path = os.path.join(config_path, test_properties_filename)
        properties.save(properties_path)
        config_instance['properties_path'] = \
            os.path.join(config_path_relative, test_properties_filename)

    persistence['configuration'][configuration_uuid] = config_instance

    return_json = {
        'configuration': {
            'uuid': configuration_uuid,
            'entry': config_instance
        }
    }

    return jsonify(return_json), 201


# Get/Delete Configuration
@plugin.route('/configuration/<string:config_uuid>/', methods=['GET', 'DELETE'])
def configuration_get_delete(config_uuid):
    if config_uuid in persistence['configuration']:
        if request.method == 'GET':
            return_json = {
                'configuration': {
                    'uuid': config_uuid,
                    'entry': persistence['configuration'][config_uuid]
                }
            }
            return jsonify(return_json), 200

        if request.method == 'DELETE':
            del persistence['configuration'][config_uuid]
            shutil.rmtree(os.path.join(storage_path, config_uuid))
            return 'Successfully deleted ' + config_uuid + '.', 200

    else:
        return "No configuration with that ID found", 404


# Run load test (param: configuration uuid)
@plugin.route('/execution/', methods=['POST'])
def execution():
    execution_instance = {}

    if 'config_uuid' in request.form:
        config_uuid = request.form['config_uuid']
        config_entry = persistence['configuration'][config_uuid]
        execution_instance['config'] = config_entry

        # Create UUID for execution
        execution_uuid = str(uuid.uuid4())
        execution_instance['uuid'] = execution_uuid

        # Execution folder will be below configuration folder
        execution_path = os.path.join(storage_path, config_uuid, execution_uuid)

        # '-n' cli mode (mandatory)
        # '-e' generate report dashboard
        # '-o' output folder for report dashboard
        # '-j' run log file name
        # '-l' test sample results filename
        jmeter_cli_call = [jmeter_executable, '-n', '-e',
                           '-o ' + os.path.join(execution_path, test_results_dashboard_folder_name),
                           '-j ' + os.path.join(execution_path, test_run_log_filename),
                           '-l ' + os.path.join(execution_path, test_sample_results_filename)]

        # Possible extensions
        # * -r -R remote (server mode)
        # * -H -P Proxy
        # * many more ( jmeter -? )
        # * Parameter string for -Dpropkey=propvalue

        if 'host' in config_entry:
            jmeter_target_host = config_entry['host']
            current_app.logger.info(f'Setting host to {jmeter_target_host}')
            jmeter_cli_call.append('-JHOST=' + jmeter_target_host)

        if 'port' in config_entry:
            jmeter_target_port = config_entry['port']
            current_app.logger.info(f'Setting port to {jmeter_target_port}')
            jmeter_cli_call.append('-JPORT=' + jmeter_target_port)

        if 'test_plan' in config_entry:
            os.mkdir(execution_path)

            jmeter_cli_call.append('-t ' + os.path.join(storage_path, config_entry['test_plan']))

            if 'properties_path' in config_entry:
                jmeter_cli_call.append('-p ' + os.path.join(config_entry['properties_path']))

        else:
            return "Configuration does not contain a test plan.", 404

        execution_instance['cli_call'] = jmeter_cli_call

        current_app.logger.info(f'JMeter CLI call: {str(jmeter_cli_call)}')

        execution_start = datetime.datetime.now()
        os.system(' '.join(jmeter_cli_call))
        execution_end = datetime.datetime.now()

        execution_instance['execution_start'] = execution_start
        execution_instance['execution_end'] = execution_end

        with tempfile.NamedTemporaryFile() as tf:
            tmp_zip_file = shutil.make_archive(tf.name, 'zip', execution_path)
            shutil.copy2(tmp_zip_file, os.path.join(execution_path, result_zip_file_name))

        persistence['execution'][execution_uuid] = execution_instance

        return jsonify(execution_instance), 201

    else:
        return "No configuration with that ID found.", jsonify(persistence), 404


# Get load test results
@plugin.route('/execution/<string:exec_uuid>/', methods=['GET'])
def execution_results(exec_uuid):
    try:
        config_uuid = persistence.get('execution').get(exec_uuid).get('config').get('uuid')
    except AttributeError:
        return "No execution found with that ID.", 404

    results_zip_path = os.path.join(storage_path, config_uuid, exec_uuid, result_zip_file_name)
    if os.path.isfile(results_zip_path):
        return send_file(results_zip_path)
    else:
        return "No results available (yet).", 404
