# Native imports
import time
import datetime
import json
import os
import shutil
import tempfile
import uuid
import zipfile
import requests


# Module imports
from flask import Blueprint, current_app, jsonify, request, send_file
from flask_api import status

name = 'DataPipeline'
prefix = 'datapipeline'
storage_enabled = True
global storage_path

plugin = Blueprint(name, __name__)

"""
    - DataPipelineLoadTest:
        type: radon.policies.testing.DataPipelineLoadTest
        properties:
          velocity_per_minute: "60"
          hostname: "radon.s3.eu-central-1.amazonaws.com"
          port: "8080"
          ti_blueprint: "radon.blueprints.testing.NiFiTIDocker"
          resource_location: "/tmp/resources.zip"
          test_duration_sec: "60"
          test_id: "firstdptest"
        targets: [ ConsS3Bucket_1 ]
"""



def getInfo(nifi_url):
    target = nifi_url + "/resources"
    response = requests.get(target)
    return response.json()

def getGroupInfo(nifi_url, id):
    target = nifi_url + "/process-groups/"+id+"/processors"
    response = requests.get(target)
    return response.json()

def configurePipeSchedulePeriod(nifi_url, id, name, seconds_between_gen):

    group_info = getGroupInfo(nifi_url, id)
    processor_info = get_processor_info(group_info,  name)
    processor_id = processor_info['component']['id']
    revision = processor_info['revision']

    schedulingPeriod = str(seconds_between_gen) + " sec"

    configuration = {
        "revision": revision,
        "component": {
            "id": str(processor_id),
            "config": {
                "schedulingPeriod": schedulingPeriod
            }
        }
    }

    stop_uri = nifi_url + "/processors/" + processor_id

    response = requests.put(stop_uri, json = configuration)
    print(response.text)
    return

def startPipe(nifi_url, id):

    stop_uri = nifi_url + "/flow/process-groups/" + id
    response = requests.put(stop_uri, json={"id": id, 'state': "RUNNING"})
    print(response.text)
    return

def stopPipe(nifi_url, id):

    stop_uri = nifi_url + "/flow/process-groups/" + id
    response = requests.put(stop_uri, json={"id": id, 'state': "STOPPED" })
    print(response.text)

    return

def findGroupId(info, type, name):
    for item in info['resources']:
        itempath = item['identifier']
        if(itempath.startswith(type) and item['name'] == name):
            id = itempath.split('/')[-1]
            return(id)

def get_processor_info(info, name):
    for item in info['processors']:
        if(item['component']['name'] == name):
            return item




def register(app, plugin_storage_path=None):
    app.register_blueprint(plugin, url_prefix=f'/{prefix}')
    app.logger.info(f'{name} plugin registered.')
    global storage_path
    storage_path= plugin_storage_path


persistence = {
    "configuration": {},
    "execution": {},
}

resources_filename = "resources.zip"

# Folder in local storage where configuration artifacts are stored
# (e.g., <storage_path>/<config_uuid>/<storage_config_folder_name/)
storage_config_folder_name = 'config'

result_zip_file_name = 'results.zip'

# Names of the folders in the results zip file
result_config_folder_name = 'config'
result_execution_folder_name = 'execution'

@plugin.route('/')
def index():
    return f'This is the Radon CTT Agent Data Pipeline Plugin.', status.HTTP_200_OK

############# Data Ppeline Testing Plugin #############

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

    # data = {'host': sut_hostname, 'test_duration_sec': test_duration_sec, 'velocity_per_minute': velocity_per_minute}
    # files = {'resources': open(resources, 'rb')}

    # Host (form)
    if 'host' in request.form:
        host = request.form.get('host', type=str)
        current_app.logger.info(f'\'host\' set to: {host}')
        config_instance['host'] = host

    # test_duration_sec (form)
    if 'test_duration_sec' in request.form:
        test_duration_sec = request.form.get('test_duration_sec', type=int)
        current_app.logger.info(f'\'test_duration_sec\' set to: {test_duration_sec}')
        config_instance['test_duration_sec'] = test_duration_sec

    # velocity_per_minute (form)
    if 'velocity_per_minute' in request.form:
        velocity_per_minute = request.form.get('velocity_per_minute', type=int)
        current_app.logger.info(f'\'velocity_per_minute\' set to: {velocity_per_minute}')
        config_instance['velocity_per_minute'] = velocity_per_minute
    # resources (file)
    data_archive_path = None


    if 'resources' in request.files:
        # Get file from request
        resources_file = request.files['resources']
        resources_zip_path = os.path.join(config_path, resources_filename)
        resources_file.save(resources_zip_path)


        # Extract resources
        resources_extract_dir = os.path.join(config_path, 'resources')
        os.makedirs(resources_extract_dir)
        with zipfile.ZipFile(resources_zip_path, 'r') as res_zip:
            res_zip.extractall(resources_extract_dir)

    else:
        return 'No resources archive location provided.', status.HTTP_400_BAD_REQUEST


    persistence['configuration'][configuration_uuid] = config_instance

    return_json = {
        'configuration': {
            'uuid': configuration_uuid,
            'entry': config_instance
        }
    }

    return jsonify(return_json), status.HTTP_201_CREATED


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
            return jsonify(return_json), status.HTTP_200_OK

        if request.method == 'DELETE':
            del persistence['configuration'][config_uuid]
            shutil.rmtree(os.path.join(storage_path, config_uuid))
            return 'Successfully deleted ' + config_uuid + '.', status.HTTP_200_OK

    else:
        return "No configuration with that ID found", status.HTTP_404_NOT_FOUND


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
        resources_path = os.path.join(storage_path, config_uuid, 'config/resources/')


        test_execution_cli_command = ["cp", resources_path+"/*", "/tmp/nifi_agent/"]

        if 'host' in config_entry:
            target_host = config_entry['host']
            current_app.logger.info(f'Setting host to {target_host}')
        else:
            return "Configuration does not contain a host value.", status.HTTP_404_NOT_FOUND

        if 'test_duration_sec' in config_entry:
            test_duration_sec = config_entry['test_duration_sec']
            current_app.logger.info(f'Setting test_duration_sec to {test_duration_sec}')
        else:
            return "Configuration does not contain a test_duration_sec value.", status.HTTP_404_NOT_FOUND

        if 'velocity_per_minute' in config_entry:
            velocity_per_minute = config_entry['velocity_per_minute']
            current_app.logger.info(f'Setting velocity_per_minute to {velocity_per_minute}')
        else:
            return "Configuration does not contain a test_duration_sec value.", status.HTTP_404_NOT_FOUND

        if 'host' in config_entry:
            target_host = config_entry['host']
            current_app.logger.info(f'Setting host to {target_host}')
        else:
            return "Configuration does not contain a host value.", status.HTTP_404_NOT_FOUND


        os.mkdir(execution_path)


        execution_instance['cli_call'] = test_execution_cli_command + [">",os.path.join(execution_path,"out.log")]
        current_app.logger.info(f'CLI call: {str(test_execution_cli_command)}')


        #access NiFi through docker host
        nifihost = "172.17.0.1"
        nifiport = "8080"
        nifi_url = "http://"+nifihost+":" + nifiport+"/nifi-api"

        #Data pipeline blocks inside the TI
        processor_group_name = "S3Bucket_dest_PG_LocalConn"
        processor_name = "PutS3Object"

        #Fetch  current information from API about running services
        nifi_info = getInfo(nifi_url)

        #Get processor group id by name
        id = findGroupId(nifi_info, "/process-groups/", processor_group_name)

        #stop the pipeline
        stopPipe(nifi_url, id)

        # Copy files to input of the pipeline
        os.system(' '.join(test_execution_cli_command))

        #configure the pipeline
        seconds_between_gen = round(60 / velocity_per_minute, 3)
        configurePipeSchedulePeriod(nifi_url, id, processor_name, seconds_between_gen)

        execution_start = datetime.datetime.now()

        #start the pipeline
        startPipe(nifi_url, id)

        #wait for the test duration
        time.sleep(test_duration_sec)

        execution_end = datetime.datetime.now()


        execution_instance['execution_start'] = execution_start
        execution_instance['execution_end'] = execution_end

        with tempfile.NamedTemporaryFile() as tf:
            tmp_zip_file = shutil.make_archive(tf.name, 'zip', execution_path)
            shutil.copy2(tmp_zip_file, os.path.join(execution_path, result_zip_file_name))

        persistence['execution'][execution_uuid] = execution_instance

        return jsonify(execution_instance), status.HTTP_201_CREATED

    else:
        return "No configuration with that ID found.", jsonify(persistence), status.HTTP_404_NOT_FOUND


# Get load test results
@plugin.route('/execution/<string:exec_uuid>/', methods=['GET'])
def execution_results(exec_uuid):
    try:
        config_uuid = persistence.get('execution').get(exec_uuid).get('config').get('uuid')
    except AttributeError:
        return "No execution found with that ID.", status.HTTP_404_NOT_FOUND

    results_zip_path = os.path.join(storage_path, config_uuid, exec_uuid, result_zip_file_name)
    if os.path.isfile(results_zip_path):
        return send_file(results_zip_path)
    else:
        return "No results available (yet).", status.HTTP_404_NOT_FOUND

