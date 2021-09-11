import logging
import subprocess
import os
import sys
import yaml

from time import sleep
from shutil import copy
from pprint import PrettyPrinter

from volttron.platform.agent.known_identities import PLATFORM_WEB
from volttron.platform import set_home, certs
from volttron.platform.instance_setup import setup_rabbitmq_volttron
from volttron.utils import get_hostname

logging.basicConfig(level=logging.DEBUG)

# The environment variables must be set or we have big issues
VOLTTRON_ROOT = os.environ["VOLTTRON_ROOT"]
VOLTTRON_HOME = os.environ["VOLTTRON_HOME"]
MESSAGE_BUS = os.environ["MESSAGE_BUS"]
if MESSAGE_BUS == "rmq":
    RMQ_SETUP_TYPE = os.environ["SETUP_TYPE"]
RMQ_HOME = os.environ["RMQ_HOME"]
VOLTTRON_CMD = "volttron"
VOLTTRON_CTL_CMD = "volttron-ctl"
VOLTTRON_CFG_CMD = "vcfg"
INSTALL_PATH = "{}/scripts/install-agent.py".format(VOLTTRON_ROOT)
KEYSTORES = os.path.join(VOLTTRON_HOME, "keystores")
if not VOLTTRON_HOME:
    VOLTTRON_HOME = "/home/volttron/.volttron"


def get_platform_config_path():
    platform_config = None
    if "PLATFORM_CONFIG" in os.environ and os.environ["PLATFORM_CONFIG"]:
        print(
            f"Using platform configuration from env var: {os.environ['PLATFORM_CONFIG']} "
        )
        platform_config = os.environ["PLATFORM_CONFIG"]
    elif os.path.isfile("/platform_config.yml"):
        print("Configuring platform from mounted volume platform_configs")
        platform_config = "/platform_config.yml"

    # Stop processing if platform config hasn't been specified
    if platform_config is None:
        sys.stderr.write("No platform configuration specified.")
        sys.exit(0)
    return platform_config


def get_platform_configurations(platform_config_path):
    with open(platform_config_path) as cin:
        config = yaml.safe_load(cin)
        agents = config["agents"]
        platform_cfg = config["config"]

    print("Platform instance name set to: {}".format(platform_cfg.get("instance-name")))

    return config, agents, platform_cfg


def configure_platform(platform_cfg):
    # Create the main volttron config file
    if not os.path.isdir(VOLTTRON_HOME):
        os.makedirs(VOLTTRON_HOME)

    # configure the volttron platform using the platform configuration in the platform_configX.yml file
    cfg_path = os.path.join(VOLTTRON_HOME, "config")
    if not os.path.exists(cfg_path):
        if len(platform_cfg):
            with open(os.path.join(cfg_path), "w") as fout:
                fout.write("[volttron]\n")
                for key, value in platform_cfg.items():
                    if key != "message-bus":
                        fout.write("{}={}\n".format(key.strip(), value.strip()))
                    else:
                        # since the value for "message-bus" is an environment variable, we have to get it through os.environ. Otherwise, the value will be a literal (e.g. $MESSAGE_BUS)
                        fout.write("{}={}\n".format(key.strip(), MESSAGE_BUS))
        # configure the volttron platform to create CA cert
        # use copied code from ~$HOME/volttron/platform/instance_setup.py
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

        if MESSAGE_BUS == "rmq":
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

        print("Creating new web server certificate.")
        print(
            "Creating and signing new certificate using the newly created CA certificate."
        )
        name = f"{platform_cfg.get('instance-name')}-{PLATFORM_WEB}"
        crts.create_signed_cert_files(
            name=name + "-server",
            cert_type="server",
            ca_name=crts.root_ca_name,
            fqdn=get_hostname(),
        )
        master_web_cert = os.path.join(
            VOLTTRON_HOME, "certificates/certs/", name + "-server.crt"
        )
        master_web_key = os.path.join(
            VOLTTRON_HOME, "certificates/private/", name + "-server.pem"
        )
        print("Writing ssl cert and key paths to config.")
        with open(os.path.join(cfg_path), "a") as fout:
            fout.write(f"web-ssl-cert = {master_web_cert}\n")
            fout.write(f"web-ssl-key = {master_web_key}\n")


def configure_message_bus(config):
    print(f"Message bus: {MESSAGE_BUS}")
    # RMQ requires additional setup
    if MESSAGE_BUS == "rmq":
        # validation checks
        if not RMQ_SETUP_TYPE:
            sys.stderr.write(
                "Configuring platform with RabbitMQ requires a setup_type, which is one of single or shovel"
            )
            sys.exit(1)
        if not config.get("rabbitmq-config"):
            sys.stderr.write(
                "Invalid rabbit-config entry in platform configuration file.\n"
            )
            sys.exit(1)

        # Step 1: Update the rabbit configuration in  rabbitmq_config.yml
        ## Get rabbitmq-config
        rabbitcfg_file = os.path.expandvars(
            os.path.expanduser(config.get("rabbitmq-config"))
        )
        if not os.path.isfile(rabbitcfg_file):
            sys.stderr.write("Invalid rabbit-config entry {} \n".format(rabbitcfg_file))
            sys.exit(1)

        with open(rabbitcfg_file) as cin:
            rabbit_config = yaml.safe_load(cin)

        # Update 'host'
        with open("/etc/hostname") as hostfile:
            hostname = hostfile.read().strip()
        rabbit_config["host"] = hostname

        # Update 'use-existing-certs'
        certs_test_path = os.path.join(
            VOLTTRON_HOME,
            "certificates/certs/{}-trusted-cas.crt".format(
                platform_cfg.get("instance-name")
            ),
        )
        if os.path.isfile(certs_test_path):
            rabbit_config["use-existing-certs"] = True

        ## Update 'rmq_home'
        rabbit_config["rmq-home"] = RMQ_HOME

        ## Update 'common-name'
        rabbit_config["certificate-data"][
            "common-name"
        ] = f"{platform_cfg.get('instance-name')}-root-ca"

        # Step 2: Write rabbit_config to the container at VOLTTRON_HOME
        ## the rabbitfilename must be set to rabbitmq_config.yml because RMQConfig class is searching for 'rabbitmq_config.yml'
        ## see constructor for RMQConfig class in volttron/utils/rmq_config_params.py
        rabbitfilename = os.path.join(VOLTTRON_HOME, "rabbitmq_config.yml")
        print(f"Creating rabbitmq config file at {rabbitfilename}")
        PrettyPrinter().pprint(f"dumpfile is :{rabbit_config}")

        with open(rabbitfilename, "w") as outfile:
            yaml.dump(rabbit_config, outfile, default_flow_style=False)
        assert os.path.isfile(rabbitfilename)

        print("Setting up rabbitmq for the first time...")
        now_dir = os.getcwd()
        os.chdir(VOLTTRON_ROOT)
        setup_rabbitmq_volttron(
            "single", True, instance_name=platform_cfg.get("instance-name")
        )

        os.chdir(now_dir)


def install_agents(agents):
    need_to_install = {}
    print("Available agents that are needing to be setup/installed")
    print(agents)

    for identity, specs in agents.items():
        path_to_keystore = os.path.join(KEYSTORES, identity)
        if not os.path.exists(path_to_keystore):
            need_to_install[identity] = specs

    # if we need to do installs, then we haven't setup this at all.
    if need_to_install:
        # Start volttron first because we can't install anything without it
        proc = subprocess.Popen([VOLTTRON_CMD, "-vv"])
        assert proc is not None
        sleep(20)

        os.path.join("configs")
        for identity, spec in need_to_install.items():
            sys.stdout.write("Processing identity: {}\n".format(identity))
            if (
                MESSAGE_BUS == "rmq"
                and RMQ_SETUP_TYPE == "shovel"
                and identity == "platform.forwardhistorian"
            ):
                print(
                    f"Platform running RMQ shovel, ForwardHistorian agent not needed."
                )
                continue

            if "source" not in spec:
                sys.stderr.write("Invalid source for identity: {}\n".format(identity))
                continue

            # Get agent configuration
            agent_cfg = None
            if "config" in spec and spec["config"]:
                agent_cfg = os.path.abspath(
                    os.path.expandvars(os.path.expanduser(spec["config"]))
                )
                if not os.path.exists(agent_cfg):
                    sys.stderr.write(
                        "Invalid config ({}) for agent id identity: {}\n".format(
                            agent_cfg, identity
                        )
                    )
                    continue

            agent_source = os.path.expandvars(os.path.expanduser(spec["source"]))

            # Get agent source
            if not os.path.exists(agent_source):
                sys.stderr.write(
                    "Invalid agent source ({}) for agent id identity: {}\n".format(
                        agent_source, identity
                    )
                )
                continue

            # Get priority from the system config file
            priority = spec.get("priority", "50")

            install_cmd = ["vctl", "install", agent_source]
            install_cmd.extend(["--vip-identity", identity])
            install_cmd.extend(["--start", "--priority", priority])
            install_cmd.extend(["--agent-start-time", "30"])
            install_cmd.append("--force")
            if agent_cfg:
                install_cmd.extend(["--config", agent_cfg])

            try:
                subprocess.check_call(install_cmd)
            except subprocess.CalledProcessError as e:
                # sometimes, the install command returns an Error saying that volttron couldn't install the agent, when in fact the agent was successfully installed
                # this is most likely a bug in Volttron. For now, we are ignoring that error so that the setup of the Volttron platform does not fail and to allow Docker to start the container
                sys.stderr.write(f"IGNORING ERROR: {e}")
                continue

            if "config_store" in spec:
                sys.stdout.write("Processing config_store entries")
                for key, entry in spec["config_store"].items():
                    if "file" not in entry or not entry["file"]:
                        sys.stderr.write(
                            "Invalid config store entry file must be specified for {}".format(
                                key
                            )
                        )
                        continue
                    entry_file = os.path.expandvars(os.path.expanduser(entry["file"]))

                    if not os.path.exists(entry_file):
                        sys.stderr.write(
                            "Invalid config store file does not exist {}".format(
                                entry_file
                            )
                        )
                        continue

                    entry_cmd = [
                        VOLTTRON_CTL_CMD,
                        "config",
                        "store",
                        identity,
                        key,
                        entry_file,
                    ]
                    if "type" in entry:
                        entry_cmd.append(entry["type"])

                    subprocess.check_call(entry_cmd)


def final_platform_configurations():
    # Stop running volttron now that it is setup.
    sys.stdout.write("\n**************************************************\n")
    sys.stdout.write("SHUTTING DOWN FROM SETUP-PLATFORM.PY\n")
    sys.stdout.write("**************************************************\n")
    subprocess.call(["vctl", "shutdown", "--platform"])

    sleep(5)
    sys.exit(0)


if __name__ == "__main__":
    set_home(VOLTTRON_HOME)
    platform_config_path = get_platform_config_path()
    config, agents, platform_cfg = get_platform_configurations(platform_config_path)
    configure_platform(platform_cfg)
    configure_message_bus(config)
    install_agents(agents)
    final_platform_configurations()
