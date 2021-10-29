import subprocess
import os
import sys
import yaml

from shutil import copy
from time import sleep
from volttron.platform import set_home, certs
from volttron.platform.agent.known_identities import PLATFORM_WEB
from volttron.utils import get_hostname
from slogger import get_logger

slogger = get_logger("setup-platform", "setup-platform")

# The environment variables must be set or we have big issues
VOLTTRON_ROOT = os.environ['VOLTTRON_ROOT']
VOLTTRON_HOME = os.environ['VOLTTRON_HOME']
RMQ_HOME = os.environ["RMQ_HOME"]
VOLTTRON_CMD = "volttron"
VOLTTRON_CTL_CMD = "volttron-ctl"
VOLTTRON_CFG_CMD = "vcfg"
INSTALL_PATH = "{}/scripts/install-agent.py".format(VOLTTRON_ROOT)
KEYSTORES = os.path.join(VOLTTRON_HOME, "keystores")
AGENT_START_TIME = "10"


if not VOLTTRON_HOME:
    VOLTTRON_HOME = "/home/volttron/.volttron"


def get_platform_config_path():
    platform_config = None
    if "PLATFORM_CONFIG" in os.environ and os.environ["PLATFORM_CONFIG"]:
        platform_config = os.environ["PLATFORM_CONFIG"]
    elif os.path.isfile("/platform_config.yml"):
        platform_config = "/platform_config.yml"
    slogger.info(f"Platform_config: {platform_config}")

    # Stop processing if platform config hasn't been specified
    if platform_config is None:
        sys.stderr.write("No platform configuration specified.")
        slogger.debug("No platform configuration specified.")
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
    # install required volttdon dependencies, wheel and pyzmq, because they are not required in setup.py
    from requirements import option_requirements as opt_reqs
    for req in opt_reqs:
        package, options = req
        install_cmd = ["pip3", "install", "--no-deps"]
        if options:
            install_cmd.append("--install-option")
            install_cmd.extend(options)
        install_cmd.append(package)
        subprocess.check_call(install_cmd)

    # install web dependencies if web-enabled
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


def install_agents(agents):
    need_to_install = {}

    sys.stdout.write("Available agents that are needing to be setup/installed")
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

        envcpy = os.environ.copy()
        for identity, spec in need_to_install.items():
            slogger.info("Processing identity: {}".format(identity))
            sys.stdout.write("Processing identity: {}\n".format(identity))
            agent_cfg = None
            if "source" not in spec:
                slogger.info(f"Invalid source for identity: {identity}")
                sys.stderr.write("Invalid source for identity: {}\n".format(identity))
                continue

            if "config" in spec and spec["config"]:
                agent_cfg = os.path.abspath(
                    os.path.expandvars(os.path.expanduser(spec["config"]))
                )
                if not os.path.exists(agent_cfg):
                    slogger.info(f"Invalid config {agent_cfg} for identity {identity}")
                    sys.stderr.write(
                        "Invalid config ({}) for agent id identity: {}\n".format(
                            agent_cfg, identity
                        )
                    )
                    continue

            agent_source = os.path.expandvars(os.path.expanduser(spec["source"]))

            if not os.path.exists(agent_source):
                slogger.info(f"Invalid agent source {agent_source} for identity {identity}")
                sys.stderr.write(
                    "Invalid agent source ({}) for agent id identity: {}\n".format(
                        agent_source, identity
                    )
                )
                continue

            # grab the priority from the system config file
            priority = spec.get("priority", "50")
            tag = spec.get("tag", "all_agents")

            install_cmd = ["python3", INSTALL_PATH]
            install_cmd.extend(["--agent-source", agent_source])
            install_cmd.extend(["--vip-identity", identity])
            install_cmd.extend(["--start", "--priority", priority])
            install_cmd.extend(["--agent-start-time", AGENT_START_TIME])
            install_cmd.append("--force")
            install_cmd.extend(["--tag", tag])
            if agent_cfg:
                install_cmd.extend(["--config", agent_cfg])

            # This allows install agent to ignore the fact that we aren't running
            # form a virtual environment.
            envcpy["IGNORE_ENV_CHECK"] = "1"
            try:
                subprocess.check_call(install_cmd, env=envcpy)
            except subprocess.CalledProcessError as e:
                # sometimes, the install command returns an Error saying that volttron couldn't install the agent, when in fact the agent was successfully installed
                # this is most likely a bug in Volttron. For now, we are ignoring that error so that the setup of the Volttron platform does not fail and to allow Docker to start the container
                sys.stderr.write(f"IGNORING ERROR: {e}")
                slogger.debug(f"IGNORING ERROR: {e}")
                continue

            if "config_store" in spec:
                sys.stdout.write("Processing config_store entries")
                for key, entry in spec["config_store"].items():
                    if "file" not in entry or not entry["file"]:
                        slogger.info(f"Invalid config store entry; file must be specified for {key}")
                        sys.stderr.write(
                            "Invalid config store entry file must be specified for {}".format(
                                key
                            )
                        )
                        continue
                    entry_file = os.path.expandvars(os.path.expanduser(entry["file"]))

                    if not os.path.exists(entry_file):
                        slogger.info(f"Invalid config store file not exist: {entry_file}")
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
    # allows platform to automatically accept all incoming auth requests
    # auth_add = ["vctl", "auth", "add", "--credentials", "/.*/"]
    # slogger.info(f"Adding * creds to auth. {auth_add}")
    # subprocess.call(auth_add)

    sys.stdout.write("\n**************************************************\n")
    sys.stdout.write("SHUTTING DOWN FROM SETUP-PLATFORM.PY\n")
    slogger.info("SHUTTING DOWN FROM SETUP-PLATFORM.PY")
    sys.stdout.write("**************************************************\n")
    subprocess.call(["vctl", "shutdown", "--platform"])

    sleep(5)
    sys.exit(0)


if __name__ == "__main__":
    set_home(VOLTTRON_HOME)
    platform_config_path = get_platform_config_path()
    config, agents, platform_cfg = get_platform_configurations(platform_config_path)
    configure_platform(platform_cfg)
    install_agents(agents)
    final_platform_configurations()
#
#
# set_home(VOLTTRON_HOME)
#
# platform_config = None
# if 'PLATFORM_CONFIG' in os.environ and os.environ['PLATFORM_CONFIG']:
#     platform_config = os.environ['PLATFORM_CONFIG']
# elif os.path.isfile('/platform_config.yml'):
#     platform_config = '/platform_config.yml'
#
# # Stop processing if platform config hasn't been specified
# if platform_config is None:
#     sys.stderr.write("No platform configuration specified.")
#     sys.exit(0)
#
# with open(platform_config) as cin:
#     config = yaml.safe_load(cin)
#     agents = config['agents']
#     platform_cfg = config['config']
#
# print("Platform instance name set to: {}".format(platform_cfg.get('instance-name')))
#
# # install required volttdon dependencies, wheel and pyzmq, because they are not required in setup.py
# from requirements import option_requirements as opt_reqs
# for req in opt_reqs:
#     package, options = req
#     install_cmd = ["pip3", "install", "--no-deps"]
#     if options:
#         install_cmd.append("--install-option")
#         install_cmd.extend(options)
#     install_cmd.append(package)
#     print(f"CMCMMM: {install_cmd}")
#     subprocess.check_call(install_cmd)
#
# bind_web_address = platform_cfg.get("bind-web-address", None)
# if bind_web_address is not None:
#     print(f"Platform bind web address set to: {bind_web_address}")
#     from requirements import extras_require as extras
#     web_plt_pack = extras.get("web", None)
#     install_cmd = ["pip3", "install"]
#     install_cmd.extend(web_plt_pack)
#     if install_cmd is not None:
#         print(f"Installing packages for web platform: {web_plt_pack}")
#         subprocess.check_call(install_cmd)
#
# envcpy = os.environ.copy()
#
# # Create the main volttron config file
# if not os.path.isdir(VOLTTRON_HOME):
#     os.makedirs(VOLTTRON_HOME)
#
# cfg_path = os.path.join(VOLTTRON_HOME, "config")
# if not os.path.exists(cfg_path):
#     if len(platform_cfg) > 0:
#         with open(os.path.join(cfg_path), "w") as fout:
#             fout.write("[volttron]\n")
#             for key, value in platform_cfg.items():
#                 fout.write("{}={}\n".format(key.strip(), value.strip()))
#
# if platform_cfg.get('message-bus') == 'rmq':
#     if os.getenv('SKIP_CA_CREATE_CERTIFICATION') != 'true':
#         print("Creating CA Certificate...")
#         crts = certs.Certs()
#         data = {
#             "C": "US",
#             "ST": "WA",
#             "L": "Richmond",
#             "O": "PNNL",
#             "OU": "Volttron",
#             "CN": f"{platform_cfg.get('instance-name')}-root-ca",
#         }
#         crts.create_root_ca(overwrite=False, **data)
#         copy(crts.cert_file(crts.root_ca_name), crts.cert_file(crts.trusted_ca_name))
#
#         print(
#             "Creating and signing new certificate using the newly created CA certificate."
#         )
#
#         print(
#             "Creating Certs for server and client, which is required for the RMQ message bus."
#         )
#         (
#             root_ca_name,
#             server_name,
#             admin_client_name,
#         ) = certs.Certs.get_admin_cert_names(platform_cfg.get("instance-name"))
#         crts.create_signed_cert_files(
#             server_name, cert_type="server", fqdn=get_hostname()
#         )
#         crts.create_signed_cert_files(admin_client_name, cert_type="client")
#
#         name = f"{platform_cfg.get('instance-name')}.{PLATFORM_WEB}"
#         master_web_cert = os.path.join(VOLTTRON_HOME, 'certificates/certs/',
#                                        name + "-server.crt")
#         master_web_key = os.path.join(VOLTTRON_HOME, 'certificates/private/',
#                                       name + "-server.pem")
#         print("Writing ssl cert and key paths to config.")
#
#         with open(os.path.join(cfg_path), "r") as f:
#             if 'web-ssl-cert' in f.read():
#                 print('web-ssl-cert is already written')
#                 web_ssl = True
#             else:
#                 print('## there is no web-ssl-cert and key')
#                 web_ssl = False
#
#         with open(os.path.join(cfg_path), "a") as fout:
#             if not web_ssl:
#                 fout.write(f"web-ssl-cert = {master_web_cert}\n")
#                 fout.write(f"web-ssl-key = {master_web_key}\n")
#
#         if not config.get('rabbitmq-config'):
#             sys.stderr.write("Invalid rabbit-config entry in platform configuration file.\n")
#             sys.exit(1)
#         rabbitcfg_file = os.path.expandvars(os.path.expanduser(config.get('rabbitmq-config')))
#         if not os.path.isfile(rabbitcfg_file):
#             sys.stderr.write("Invalid rabbit-config entry {} \n".format(rabbitcfg_file))
#             sys.exit(1)
#         with open(rabbitcfg_file) as cin:
#             rabbit_config = yaml.safe_load(cin)
#         with open('/etc/hostname') as hostfile:
#             hostname = hostfile.read().strip()
#         if not hostname:
#             sys.stderr.write("Invalid hostname set, please set it in the docker-compose or in the container.")
#             sys.exit(1)
#
#         rabbit_config['host'] = hostname
#         certs_test_path = os.path.join(VOLTTRON_HOME,
#                                        "certificates/certs/{}-trusted-cas.crt".format(platform_cfg.get("instance-name")))
#         if os.path.isfile(certs_test_path):
#             rabbit_config['use-existing-certs'] = True
#
#         ## Update rmq_home
#         print(f"Setting rmq-home to {RMQ_HOME}.")
#         rabbit_config["rmq-home"] = RMQ_HOME
#
#         rabbitfilename = os.path.join(VOLTTRON_HOME, "rabbitmq_config.yml")
#         print("Creating rabbitmq conifg file at {}".format(rabbitfilename))
#         print("dumpfile is :{}".format(rabbit_config))
#         with open(rabbitfilename, 'w') as outfile:
#             yaml.dump(rabbit_config, outfile, default_flow_style=False)
#
#         assert os.path.isfile(rabbitfilename)
#     now_dir = os.getcwd()
#     os.chdir(VOLTTRON_ROOT)
#
#     setup_rabbitmq_volttron('single', True, instance_name=platform_cfg.get('instance-name'))
#     os.chdir(now_dir)
#
#
# need_to_install = {}
#
# print("Available agents that are needing to be setup/installed")
# print(agents)
#
# # TODO Fix so that the agents identities are consulted.
# for identity, specs in agents.items():
#     path_to_keystore = os.path.join(KEYSTORES, identity)
#     if not os.path.exists(path_to_keystore):
#         need_to_install[identity] = specs
#
# # if we need to do installs then we haven't setup this at all.
# if need_to_install:
#     # Start volttron first because we can't install anything without it
#     proc = subprocess.Popen([VOLTTRON_CMD, "-vv"])
#     assert proc is not None
#     sleep(20)
#
#     config_dir = os.path.join("configs")
#     for identity, spec in need_to_install.items():
#         sys.stdout.write("Processing identity: {}\n".format(identity))
#         agent_cfg = None
#         if "source" not in spec:
#             sys.stderr.write("Invalid source for identity: {}\n".format(identity))
#             continue
#
#         if "config" in spec and spec["config"]:
#             agent_cfg = os.path.abspath(
#                 os.path.expandvars(
#                     os.path.expanduser(spec['config']))) #os.path.join(config_dir, spec["config"])
#             if not os.path.exists(agent_cfg):
#                 sys.stderr.write("Invalid config ({}) for agent id identity: {}\n".format(agent_cfg, identity))
#                 continue
#
#         agent_source = os.path.expandvars(os.path.expanduser(spec['source']))
#
#         if not os.path.exists(agent_source):
#             sys.stderr.write("Invalid agent source ({}) for agent id identity: {}\n".format(agent_source, identity))
#             continue
#
#         # grab the priority from the system config file
#         priority = spec.get('priority', '50')
#
#         install_cmd = ["python3", INSTALL_PATH]
#         install_cmd.extend(["--agent-source", agent_source])
#         install_cmd.extend(["--vip-identity", identity])
#         install_cmd.extend(["--start", "--priority", priority])
#         install_cmd.extend(["--agent-start-time", "60"])
#         install_cmd.append('--force')
#         if agent_cfg:
#             install_cmd.extend(["--config", agent_cfg])
#
#         # This allows install agent to ignore the fact that we aren't running
#         # form a virtual environment.
#         envcpy['IGNORE_ENV_CHECK'] = "1"
#         try:
#             subprocess.check_call(install_cmd, env=envcpy)
#         except subprocess.CalledProcessError as e:
#             # sometimes, the install command returns an Error saying that volttron couldn't install the agent, when in fact the agent was successfully installed
#             # this is most likely a bug in Volttron. For now, we are ignoring that error so that the setup of the Volttron platform does not fail and to allow Docker to start the container
#             sys.stderr.write(f"IGNORING ERROR: {e}")
#             continue
#
#         if "config_store" in spec:
#             sys.stdout.write("Processing config_store entries")
#             for key, entry in spec['config_store'].items():
#                 if 'file' not in entry or not entry['file']:
#                     sys.stderr.write("Invalid config store entry file must be specified for {}".format(key))
#                     continue
#                 entry_file = os.path.expandvars(os.path.expanduser(entry['file']))
#
#                 if not os.path.exists(entry_file):
#                     sys.stderr.write("Invalid config store file does not exist {}".format(entry_file))
#                     continue
#
#                 entry_cmd = [VOLTTRON_CTL_CMD, "config", "store", identity, key, entry_file]
#                 if "type" in entry:
#                     entry_cmd.append(entry['type'])
#
#                 subprocess.check_call(entry_cmd)
#
#     # Stop running volttron now that it is setup.
#     sys.stdout.write("\n**************************************************\n")
#     sys.stdout.write("SHUTTING DOWN FROM SETUP-PLATFORM.PY\n")
#     sys.stdout.write("**************************************************\n")
#     subprocess.call(["vctl", "shutdown", "--platform"])
#
#     sleep(5)
#     sys.exit(0)
