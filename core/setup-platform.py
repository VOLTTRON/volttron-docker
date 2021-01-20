import logging
import subprocess
import os
import sys
from shutil import copy
import yaml
from time import sleep

from volttron.platform.agent.known_identities import MASTER_WEB
from volttron.platform import set_home, certs
from volttron.platform.instance_setup import setup_rabbitmq_volttron
from volttron.utils import get_hostname

logging.basicConfig(level=logging.DEBUG)

# The environment variables must be set or we have big issues
VOLTTRON_ROOT = os.environ['VOLTTRON_ROOT']
VOLTTRON_HOME = os.environ['VOLTTRON_HOME']
RMQ_HOME = os.environ["RMQ_HOME"]
VOLTTRON_CMD = "volttron"
VOLTTRON_CTL_CMD = "volttron-ctl"
VOLTTRON_CFG_CMD = "vcfg"
INSTALL_PATH = "{}/scripts/install-agent.py".format(VOLTTRON_ROOT)
KEYSTORES = os.path.join(VOLTTRON_HOME, "keystores")

if not VOLTTRON_HOME:
    VOLTTRON_HOME = "/home/volttron/.volttron"

set_home(VOLTTRON_HOME)

platform_config = None
if 'PLATFORM_CONFIG' in os.environ and os.environ['PLATFORM_CONFIG']:
    platform_config = os.environ['PLATFORM_CONFIG']
elif os.path.isfile('/platform_config.yml'):
    platform_config = '/platform_config.yml'

# Stop processing if platform config hasn't been specified
if platform_config is None:
    sys.stderr.write("No platform configuration specified.")
    sys.exit(0)

with open(platform_config) as cin:
    config = yaml.safe_load(cin)
    agents = config['agents']
    platform_cfg = config['config']

print("Platform instance name set to: {}".format(platform_cfg.get('instance-name')))

bind_web_address = platform_cfg.get("bind-web-address", None)
if bind_web_address is not None:
    print(f"Platform bind web address set to: {bind_web_address}")
    from requirements import extras_require as extras
    web_plt_pack = extras.get("web", None)
    install_cmd = ["pip3", "install"]
    install_cmd.extend(web_plt_pack)
    if install_cmd is not None:
        print(f"Installing packages for web platform: {web_plt_pack}")
        subprocess.check_call(install_cmd)

envcpy = os.environ.copy()

# Create the main volttron config file
if not os.path.isdir(VOLTTRON_HOME):
    os.makedirs(VOLTTRON_HOME)

cfg_path = os.path.join(VOLTTRON_HOME, "config")
if not os.path.exists(cfg_path):
    if len(platform_cfg) > 0:
        with open(os.path.join(cfg_path), "w") as fout:
            fout.write("[volttron]\n")
            for key, value in platform_cfg.items():
                fout.write("{}={}\n".format(key.strip(), value.strip()))

if platform_cfg.get('message-bus') == 'rmq':
    print("Creating CA Certificate...")
    crts = certs.Certs()
    data = {
        "C": "US",
        "ST": "WA",
        "L": "Richmond",
        "O": "PNNL",
        "OU": "Volttron",
        "CN": f"{platform_cfg.get('instance-name')}-root-ca",
    }
    crts.create_root_ca(overwrite=False, **data)
    copy(crts.cert_file(crts.root_ca_name), crts.cert_file(crts.trusted_ca_name))

    print(
        "Creating and signing new certificate using the newly created CA certificate."
    )

    print(
        "Creating Certs for server and client, which is required for the RMQ message bus."
    )
    (
        root_ca_name,
        server_name,
        admin_client_name,
    ) = certs.Certs.get_admin_cert_names(platform_cfg.get("instance-name"))
    crts.create_signed_cert_files(
        server_name, cert_type="server", fqdn=get_hostname()
    )
    crts.create_signed_cert_files(admin_client_name, cert_type="client")

    name = f"{platform_cfg.get('instance-name')}.{MASTER_WEB}"
    master_web_cert = os.path.join(VOLTTRON_HOME, 'certificates/certs/',
                                   name + "-server.crt")
    master_web_key = os.path.join(VOLTTRON_HOME, 'certificates/private/',
                                  name + "-server.pem")
    print("Writing ssl cert and key paths to config.")
    with open(os.path.join(cfg_path), "a") as fout:
        fout.write(f"web-ssl-cert = {master_web_cert}\n")
        fout.write(f"web-ssl-key = {master_web_key}\n")

    if not config.get('rabbitmq-config'):
        sys.stderr.write("Invalid rabbit-config entry in platform configuration file.\n")
        sys.exit(1)
    rabbitcfg_file = os.path.expandvars(os.path.expanduser(config.get('rabbitmq-config')))
    if not os.path.isfile(rabbitcfg_file):
        sys.stderr.write("Invalid rabbit-config entry {} \n".format(rabbitcfg_file))
        sys.exit(1)
    with open(rabbitcfg_file) as cin:
        rabbit_config = yaml.safe_load(cin)
    with open('/etc/hostname') as hostfile:
        hostname = hostfile.read().strip()
    if not hostname:
        sys.stderr.write("Invalid hostname set, please set it in the docker-compose or in the container.")
        sys.exit(1)

    rabbit_config['host'] = hostname
    certs_test_path = os.path.join(VOLTTRON_HOME,
                                   "certificates/certs/{}-trusted-cas.crt".format(platform_cfg.get("instance-name")))
    if os.path.isfile(certs_test_path):
        rabbit_config['use-existing-certs'] = True

    ## Update rmq_home
    print(f"Setting rmq-home to {RMQ_HOME}.")
    rabbit_config["rmq-home"] = RMQ_HOME

    rabbitfilename = os.path.join(VOLTTRON_HOME, "rabbitmq_config.yml")
    print("Creating rabbitmq conifg file at {}".format(rabbitfilename))
    print("dumpfile is :{}".format(rabbit_config))
    with open(rabbitfilename, 'w') as outfile:
        yaml.dump(rabbit_config, outfile, default_flow_style=False)

    assert os.path.isfile(rabbitfilename)
    now_dir = os.getcwd()
    os.chdir(VOLTTRON_ROOT)

    setup_rabbitmq_volttron('single', True, instance_name=platform_cfg.get('instance-name'))
    
    os.chdir(now_dir)


need_to_install = {}

print("Available agents that are needing to be setup/installed")
print(agents)

# TODO Fix so that the agents identities are consulted.
for identity, specs in agents.items():
    path_to_keystore = os.path.join(KEYSTORES, identity)
    if not os.path.exists(path_to_keystore):
        need_to_install[identity] = specs

# if we need to do installs then we haven't setup this at all.
if need_to_install:
    # Start volttron first because we can't install anything without it
    proc = subprocess.Popen([VOLTTRON_CMD, "-vv"])
    assert proc is not None
    sleep(20)

    config_dir = os.path.join("configs")
    for identity, spec in need_to_install.items():
        sys.stdout.write("Processing identity: {}\n".format(identity))
        agent_cfg = None
        if "source" not in spec:
            sys.stderr.write("Invalid source for identity: {}\n".format(identity))
            continue

        if "config" in spec and spec["config"]:
            agent_cfg = os.path.abspath(
                os.path.expandvars(
                    os.path.expanduser(spec['config']))) #os.path.join(config_dir, spec["config"])
            if not os.path.exists(agent_cfg):
                sys.stderr.write("Invalid config ({}) for agent id identity: {}\n".format(agent_cfg, identity))
                continue

        agent_source = os.path.expandvars(os.path.expanduser(spec['source']))

        if not os.path.exists(agent_source):
            sys.stderr.write("Invalid agent source ({}) for agent id identity: {}\n".format(agent_source, identity))
            continue

        # grab the priority from the system config file
        priority = spec.get('priority', '50')

        install_cmd = ["python3", INSTALL_PATH]
        install_cmd.extend(["--agent-source", agent_source])
        install_cmd.extend(["--vip-identity", identity])
        install_cmd.extend(["--start", "--priority", priority])
        install_cmd.extend(["--agent-start-time", "20"])
        install_cmd.append('--force')
        if agent_cfg:
            install_cmd.extend(["--config", agent_cfg])

        # This allows install agent to ignore the fact that we aren't running
        # form a virtual environment.
        envcpy['IGNORE_ENV_CHECK'] = "1"
        subprocess.check_call(install_cmd, env=envcpy)

        if "config_store" in spec:
            sys.stdout.write("Processing config_store entries")
            for key, entry in spec['config_store'].items():
                if 'file' not in entry or not entry['file']:
                    sys.stderr.write("Invalid config store entry file must be specified for {}".format(key))
                    continue
                entry_file = os.path.expandvars(os.path.expanduser(entry['file']))

                if not os.path.exists(entry_file):
                    sys.stderr.write("Invalid config store file does not exist {}".format(entry_file))
                    continue

                entry_cmd = [VOLTTRON_CTL_CMD, "config", "store", identity, key, entry_file]
                if "type" in entry:
                    entry_cmd.append(entry['type'])

                subprocess.check_call(entry_cmd)

    # Stop running volttron now that it is setup.
    sys.stdout.write("\n**************************************************\n")
    sys.stdout.write("SHUTTING DOWN FROM SETUP-PLATFORM.PY\n")
    sys.stdout.write("**************************************************\n")
    subprocess.call(["vctl", "shutdown", "--platform"])

    sleep(5)
    sys.exit(0)
