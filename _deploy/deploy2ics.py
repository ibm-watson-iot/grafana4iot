from subprocess import Popen, PIPE
from collections import namedtuple
import json
import time
import argparse

# See: https://gist.github.com/markhu/fbbab71359af00e527d0
class edict(dict):
    # based on class dotdict(dict):  # from http://stackoverflow.com/questions/224026/dot-notation-for-dictionary-keys
    
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

    def __init__(self, data):
        if type(data) == str:
            data = json.loads( data)
        for name, value in data.iteritems():
            setattr(self, name, self._wrap(value))

    def __getattr__(self, attr):
        return self.get(attr, None)

    def _wrap(self, value):  # from class Struct by XEye '11 http://stackoverflow.com/questions/1305532/convert-python-dict-to-object
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])  # recursion!
        else:
            if isinstance(value, dict):
                return edict(value)  # is there a relative way to get class name?
            else:
                return value

# Adapted from: https://gist.github.com/mminer/a08566f13ef687c17b39
COLUMNS = [
    'CONTAINER ID',
    'IMAGE',
    'COMMAND',
    'CREATED',
    'STATUS',
    'PORTS',
    'NAMES',
]

ColumnRange = namedtuple('ColumnRange', ['column', 'start_idx', 'stop_idx'])

def find_column_range(header, column):
    """Determines the string indexes that the given column lies between."""
    column_idx = COLUMNS.index(column)
    start_idx = header.index(column)

    try:
        next_column = COLUMNS[column_idx + 1]
        stop_idx = header.index(next_column)
    except IndexError:
        # There is no next column (i.e. we're on the last one).
        stop_idx = None

    column_range = ColumnRange(column, start_idx, stop_idx)
    return column_range


def row_to_container(row, column_ranges):
    """Extracts the column values from a container row."""
    container = {column_range.column: extract_field(row, column_range) for column_range in column_ranges}
    return container


def extract_field(row, column_range):
    """Pulls the value of a field from a given row."""
    start_idx = column_range.start_idx
    stop_idx = column_range.stop_idx or len(row)
    field = row[start_idx:stop_idx].strip()
    return field


# -----------------------------------------------------------------------------


def runCmd(cmdArray):
    p = Popen(cmdArray, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
    output, error = p.communicate()
    return [p.returncode, output, error]


def cfLogin(apiEndpoint, username, password, organization, space):
    print("Logging in to cf @ %s ..." % apiEndpoint)
    resp = runCmd(["cf", "login", "-a", apiEndpoint, "-u", username, "-p", password, "-o", organization, "-s", space])
    if resp[0] == 0:
        print("Logged into %s/%s @ %s as %s" % (organization, space, apiEndpoint, username))
    else:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to login to %s/%s @ %s as %s" % (organization, space, apiEndpoint, username))

def icsLogin():
    print("Logging in to ics ...")
    resp = runCmd(["cf", "ic", "login"])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])

def icsPush(image, cfRegistry, cfNamespace):
    source = image
    destination = cfRegistry + "/" + cfNamespace + "/" + image + ":latest"
    
    print("Tagging docker image %s ..." % destination)
    resp = runCmd(["docker", "tag", "-f", source, destination])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to tag")
    
    print("Pushing docker image %s to ICS ..." % destination)
    resp = runCmd(["docker", "push", destination])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to push")

def icsStop(containerName):
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    
    print("Stopping container %s ..." % containerName)
    resp = runCmd(["cf", "ic", "stop", containerName])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to stop %s" % containerName)

def icsWait(containerName):
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    
    print("Waiting for container %s to stop ..." % containerName)
    resp = runCmd(["cf", "ic", "wait", containerName])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to wait for %s" % containerName)

def icsRemove(containerName):
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    
    print("Removing container %s ..." % containerName)
    resp = runCmd(["cf", "ic", "rm", containerName])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to wait for %s" % containerName)

def icsGetVolumes():
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    
    resp = runCmd(["cf", "ic", "volume", "list"])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to list volumes")
    else:
        print(resp[1])
        return resp[1].decode('utf-8').splitlines()

def icsGetContainers():
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    containers = []
    
    resp = runCmd(["cf", "ic", "ps", "-a", "--no-trunc"])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to list volumes")
    else:
        lines = resp[1].decode('utf-8').splitlines()
        header = lines.pop(0)
        if len(lines) > 0:
            column_ranges = [find_column_range(header, column) for column in COLUMNS]
            ps_output = [row_to_container(row, column_ranges) for row in lines]
            for container in ps_output:
                containers.append(container['NAMES'])
        return containers

def icsCreateVolume(volumeName):
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    
    print("Creating volume %s ..." % volumeName)
    resp = runCmd(["cf", "ic", "volume", "create", volumeName])
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to create volume %s" % volumeName)
    

def icsWaitForDelete(containerName, retries=10):
    print("Waiting for container %s to be deleted (%s retries remaining) ..." % (containerName, retries))
    containers = icsGetContainers()
    if containerName in containers:
        time.sleep(10)
        if retries > 0:
            icsWaitForDelete(containerName, retries-1)
        else:
            raise Exception("Timed out waiting for container %s to be deleted" % containerName)
        
def icsRun(runArray):
    # https://www.ng.bluemix.net/docs/containers/container_creating_ov.html#container_single_cli
    
    print("Running %s ..." % " ".join(runArray))
    resp = runCmd(["cf", "ic", "run"] + runArray)
    if resp[0] != 0:
        print(resp[1])
        print(resp[2])
        raise Exception("Unable to run %s" % " ".join(runArray))

# Go Go Go!

# =============================================================================
# Initialize the properties we need
# =============================================================================
parser = argparse.ArgumentParser()
parser.add_argument('-e', '--endpoint', required=True)
parser.add_argument('-u', '--username', required=True)
parser.add_argument('-p', '--password', required=True)
parser.add_argument('-o', '--organization', required=True)
parser.add_argument('-s', '--space', required=True)

args, unknown = parser.parse_known_args()

# =============================================================================
# Load Configuration
# =============================================================================
with open('ics_config.json') as data_file:
    config_dict = json.load(data_file)

name = 'grafana4iot'
config = edict(config_dict[name])
cfImage = config.ics.registry + "/" + config.ics.namespace + "/" + config.source.image + ":latest"


# =============================================================================
# Login 
# =============================================================================
cfLogin(args.endpoint, args.username, args.password, args.organization, args.space)
icsLogin()

containers = icsGetContainers()

# =============================================================================
# Deploy the images to ICS registry
# =============================================================================
#icsPush(config.source.image, config.ics.registry, config.ics.namespace)

# =============================================================================
# Stop the running application instance
# =============================================================================
if name in containers:
    icsStop(name)
    icsWait(name)
    icsRemove(name)

# =============================================================================
# Run the new application instance
# =============================================================================
volumeList = icsGetVolumes()

for volumeName in config.ics.volumes:
    if volumeName not in volumeList:
        icsCreateVolume(volumeName)

icsWaitForDelete(name)
icsRun(config.ics.runOptions + ["--memory", str(config.ics.memory), "--name", name, cfImage])