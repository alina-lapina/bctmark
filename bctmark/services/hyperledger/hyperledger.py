from enoslib.api import __docker__, __python3__, __default_python3__, play_on, run_ansible
from enoslib.host import Host
from enoslib.service.service import Service
from typing import List
import os

CURRENT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))


class Hyperledger(Service):
    def __init__(
            self,
            orderers: List[Host],
            peers: List[Host],
            priors=[__python3__, __default_python3__, __docker__],
            extra_vars=None,
            **kwargs
    ):
        self.orderers = orderers
        self.peers = peers
        self.roles = {}
        self.roles.update(orderer=self.orderers, peer=self.peers)
        self.priors = priors

    def deploy(self):
        # Install prerequisite
        with play_on(pattern_hosts="all", roles=self.roles, priors=self.priors) as p:
            p.pip(display_name="Installing python-docker", name="docker")
            p.group(name="docker",
                    state="present")
            p.shell("usermod -aG docker $USER",
                    display_name="Add Ansible user to docker group")
        _playbook = os.path.join(CURRENT_PATH, "playbooks", "install_binaries.yaml")
        run_ansible([_playbook], roles=self.roles)

        # Generate certificates and config
        with play_on(pattern_hosts=self.orderers[0].alias, roles=self.roles) as p:
            p.template(
                src=os.path.join(CURRENT_PATH, "templates", "orderer_env.j2"),
                dest="/tmp/env"
            )
            p.template(
                src=os.path.join(CURRENT_PATH, "templates", "crypto-config.yaml.j2"),
                dest="/tmp/crypto-config.yaml"
            )
            p.shell("cd /tmp && cryptogen generate --config=crypto-config.yaml",
                    display_name="Generate certificates with cryptogen")

            p.template(
                src=os.path.join(CURRENT_PATH, "templates", "configtx.yaml.j2"),
                dest="/tmp/configtx.yaml"
            )
            p.shell(
                "configtxgen -profile SampleSingleMSPSolo -channelID ordererchannel -outputBlock genesis.block",
                display_name="Generate genesis with configtxgen",
                chdir="/tmp")
            p.shell(
                (
                    "configtxgen "
                    "-profile SampleSingleMSPChannel "
                    "-outputCreateChannelTx peerchannel.tx "
                    "-channelID peerchannel"
                ),
                display_name="Generate peerchannel.tx with configtxgen",
                chdir="/tmp")
            p.shell(
                (
                    "configtxgen "
                    "-profile SampleSingleMSPChannel "
                    "-outputAnchorPeersUpdate anchorPeersUpdate.tx "
                    "-channelID peerchannel "
                    "-asOrg PeerOrg"
                ),
                display_name="Generate anchor peer update transaction (anchorPeersUpdate.tx)",
                chdir="/tmp")

        _playbook = os.path.join(CURRENT_PATH, "playbooks", "fetch_crypto_config.yaml")
        run_ansible([_playbook], roles={"orderer": [self.orderers[0]]})

        # Copy artifacts
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.shell(
                "cp /tmp/hyperledger/config/core.yaml /tmp/core.yaml",
                display_name="Move core.yaml to /tmp/"
            )
            p.shell(
                "cp /tmp/hyperledger/config/orderer.yaml /tmp/orderer.yaml",
                display_name="Move orderer.yaml to /tmp/"
            )
            p.copy(
                src="/tmp/crypto-config/{{groups['orderer'][0]}}/tmp/crypto-config",
                dest="/tmp/",
                mode="u=rwx,g=rwx,o=rwx",
                display_name="Copy crypto-config"
            )
            p.copy(
                src="/tmp/anchorPeersUpdate.tx",
                dest="/tmp/anchorPeersUpdate.tx",
                mode="u=rwx,g=rwx,o=rwx",
                display_name="Copy anchorPeersUpdate.tx"
            )
            p.copy(
                src="/tmp/peerchannel.tx",
                dest="/tmp/peerchannel.tx",
                mode="u=rwx,g=rwx,o=rwx",
                display_name="Copy peerchannel.tx"
            )
            p.copy(
                src="/tmp/genesis.block",
                dest="/tmp/genesis.block",
                mode="u=rwx,g=rwx,o=rwx",
                display_name="Copy genesis.block"
            )

        # Run network
        with play_on(pattern_hosts="orderer", roles=self.roles) as p:
            crypdir = "/tmp/crypto-config/ordererOrganizations/ordererorg.example.com/orderers/{{ntw_monitoring_ip}}"

            p.shell(
                "nohup orderer > /tmp/orderer.out 2>&1 &",
                display_name="Run orderer",
                environment={
                    "FABRIC_CFG_PATH": "/tmp/",
                    "FABRIC_LOGGING_SPEC": "DEBUG",
                    "ORDERER_GENERAL_LISTENADDRESS": "0.0.0.0",
                    "ORDERER_GENERAL_GENESISMETHOD": "file",
                    "ORDERER_GENERAL_GENESISFILE": "/tmp/genesis.block",
                    "ORDERER_GENERAL_LOCALMSPID": "OrdererMSP",
                    "ORDERER_GENERAL_LOCALMSPDIR": "%s/msp" % crypdir,
                    "ORDERER_GENERAL_TLS_ENABLED": "true",
                    "ORDERER_GENERAL_TLS_PRIVATEKEY": "%s/tls/server.key" % crypdir,
                    "ORDERER_GENERAL_TLS_CERTIFICATE": "%s/tls/server.crt" % crypdir,
                    "ORDERER_GENERAL_TLS_ROOTCAS": "[%s/tls/ca.crt]" % crypdir,
                    "ORDERER_GENERAL_CLUSTER_CLIENTCERTIFICATE": "%s/tls/server.crt" % crypdir,
                    "ORDERER_GENERAL_CLUSTER_CLIENTPRIVATEKEY": "%s/tls/server.key" % crypdir,
                    "ORDERER_GENERAL_CLUSTER_ROOTCAS": "[%s/tls/ca.crt]" % crypdir,
                    "ORDERER_OPERATIONS_LISTENADDRESS": "localhost:8125",
                    "ORDERER_METRICS_PROVIDER": "statsd",  # statd or disabled
                    "ORDERER_METRICS_STATSD_ADDRESS": "localhost:8125",
                    "ORDERER_METRICS_STATSD_NETWORK": "udp",
                    "ORDERER_METRICS_STATSD_PREFIX": "orderer"
                }
            )

        adminpeer = self.peers[0].alias
        peercrypdir = "/tmp/crypto-config/peerOrganizations/peerorg.example.com/peers/{{ntw_monitoring_ip}}"
        adminpeercryptdir = "/tmp/crypto-config/peerOrganizations/peerorg.example.com/users/Admin@peerorg.example.com"
        boostrap_ip = "{{hostvars[groups['peer'][0]]['ntw_monitoring_ip'] if hostvars[groups['peer'][0]]['ntw_monitoring_ip'] != ntw_monitoring_ip else hostvars[groups['peer'][1]]['ntw_monitoring_ip']}}"
        peerenv = {
            "FABRIC_CFG_PATH": "/tmp/",
            "FABRIC_LOGGING_SPEC": "DEBUG",
            "CORE_PEER_ID": "{{ntw_monitoring_ip}}",
            "CORE_PEER_ADDRESS": "{{ntw_monitoring_ip}}:7051",
            "CORE_PEER_LISTENADDRESS": "0.0.0.0:7051",
            "CORE_PEER_CHAINCODEADDRESS": "{{ntw_monitoring_ip}}:7052",
            "CORE_PEER_CHAINCODELISTENADDRESS": "0.0.0.0:7052",
            "CORE_PEER_GOSSIP_BOOTSTRAP": "%s:7051" % boostrap_ip,
            "CORE_PEER_GOSSIP_EXTERNALENDPOINT": "{{ntw_monitoring_ip}}:7051",
            "CORE_PEER_LOCALMSPID": "PeerMSP",
            "CORE_PEER_MSPCONFIGPATH": "%s/msp" % peercrypdir,
            "CORE_VM_ENDPOINT": "unix:///var/run/docker.sock",
            "CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE": "host",
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_GOSSIP_USELEADERELECTION": "true",
            "CORE_PEER_GOSSIP_ORGLEADER": "false",
            "CORE_PEER_PROFILE_ENABLED": "true",
            "CORE_PEER_TLS_CERT_FILE": "%s/tls/server.crt" % peercrypdir,
            "CORE_PEER_TLS_KEY_FILE": "%s/tls/server.key" % peercrypdir,
            "CORE_PEER_TLS_ROOTCERT_FILE": "%s/tls/ca.crt" % peercrypdir,
            "CORE_CHAINCODE_EXECUTETIMEOUT": "300s",
            "CORE_METRICS_PROVIDER": "statsd",  # statd
            "CORE_METRICS_STATSD_ADDRESS": "localhost:8125",
            "CORE_OPERATIONS_LISTENADDRESS": "localhost:8125",
            "CORE_METRICS_WRITEINTERVAL": "5s",
            "CORE_METRICS_PREFIX": "peer"
        }
        adminenv = {
            "FABRIC_CFG_PATH": "/tmp/",
            "FABRIC_LOGGING_SPEC": "DEBUG",
            "CORE_PEER_ID": "{{ntw_monitoring_ip}}",
            "CORE_PEER_ADDRESS": "{{ntw_monitoring_ip}}:7051",
            "CORE_PEER_LOCALMSPID": "PeerMSP",
            "CORE_PEER_TLS_ENABLED": "true",
            "CORE_PEER_TLS_CERT_FILE": "%s/tls/server.crt" % peercrypdir,
            "CORE_PEER_TLS_KEY_FILE": "%s/tls/server.key" % peercrypdir,
            "CORE_PEER_TLS_ROOTCERT_FILE": "%s/tls/ca.crt" % peercrypdir,
            "CORE_PEER_MSPCONFIGPATH": "%s/msp" % adminpeercryptdir
        }

        with play_on(pattern_hosts="peer", roles=self.roles) as p:
            p.template(
                src=os.path.join(CURRENT_PATH, "templates", "peer_env.j2"),
                dest="/tmp/env"
            )
            p.shell(
                "nohup peer node start > /tmp/peer.out 2>&1 &",
                display_name="Run peer",
                environment=peerenv
            )

        with play_on(pattern_hosts=adminpeer, roles=self.roles) as p:
            p.shell(
                (
                    "peer channel create "
                    "-o {{hostvars[groups['orderer'][0]]['ntw_monitoring_ip']}}:7050 "
                    "-c peerchannel "
                    "-f /tmp/peerchannel.tx "
                    "--tls true "
                    "--cafile /tmp/crypto-config/ordererOrganizations/ordererorg.example.com/orderers/{{hostvars[groups['orderer'][0]]['ntw_monitoring_ip']}}/msp/tlscacerts/tlsca.ordererorg.example.com-cert.pem "
                    "--outputBlock /tmp/peerchannel.block "
                    "> /tmp/peer_channel_create.out 2>&1"
                ),
                display_name="Generate peerchannel.block",
                environment=adminenv
            )

            p.fetch(src="/tmp/peerchannel.block", dest="/tmp/peerchannel.block", flat="yes")

        with play_on(pattern_hosts="peer", roles=self.roles) as p:
            p.copy(src="/tmp/peerchannel.block", dest="/tmp/peerchannel.block")
            p.shell(
                (
                    "peer channel join -b /tmp/peerchannel.block "
                    "> /tmp/peer_channel_join.out 2>&1"
                ),
                display_name="Join Channel",
                environment=adminenv
            )
            p.copy(
                src=os.path.join(CURRENT_PATH, "chaincodes", "newcc"),
                dest="/tmp/chaincodes"
            )
            p.shell(
                (
                    "peer chaincode install "
                    "-n mycc "
                    "-v 1.0 "
                    "-p /tmp/chaincodes/newcc "
                    "-l 'node' "
                    "> /tmp/peer_chaincode_install.out 2>&1"
                ),
                display_name="Install chaincode",
                environment=adminenv
            )
        with play_on(pattern_hosts=adminpeer, roles=self.roles) as p:
             p.shell(
                 (
                     "peer chaincode instantiate "
                     "-o {{hostvars[groups['orderer'][0]]['ntw_monitoring_ip']}}:7050 "
                     "-C peerchannel "
                     "-n mycc "
                     "-l 'node' "
                     "-v 1.0 "
                     "-c '{\"Args\":[]}' "
                     "--tls true "
                     "--cafile /tmp/crypto-config/ordererOrganizations/ordererorg.example.com/orderers/{{hostvars[groups['orderer'][0]]['ntw_monitoring_ip']}}/msp/tlscacerts/tlsca.ordererorg.example.com-cert.pem "
                     "> /tmp/peer_chaincode_instantiate.out 2>&1"
                 ),
                 display_name="Instantiate chaincode",
                 environment=adminenv,
                 become="yes"
             )

        _playbook = os.path.join(CURRENT_PATH, "playbooks", "create_connection_profile.yaml")
        _connection_profile_tmpl = os.path.join(CURRENT_PATH, "templates", "network.json.j2")
        _list_orderers_ip = [h.extra['ntw_monitoring_ip'] for h in self.orderers]
        _list_peers_ip = [h.extra['ntw_monitoring_ip'] for h in self.peers]
        run_ansible(
            [_playbook],
            roles=self.roles,
            extra_vars={
                "template_src": _connection_profile_tmpl,
                'list_orderers_ip': _list_orderers_ip,
                'list_peers_ip': _list_peers_ip
            }
        )

    def destroy(self):
        with play_on(pattern_hosts="peer", roles=self.roles) as p:
            p.shell(
                "if pgrep peer; then pkill peer; fi",
                display_name="Kill peer process"
            )
            p.file(
                path="/tmp/peer*",
                state="absent",
                display_name="Delete peers logs files"
            )
        with play_on(pattern_hosts="orderer", roles=self.roles) as p:
            p.shell(
                "if pgrep orderer; then pkill orderer; fi",
                display_name="Kill orderer process"
            )
        with play_on(pattern_hosts="all", roles=self.roles) as p:
            p.file(
                path="/var/hyperledger",
                state="absent",
                display_name="Delete hyperledger blockchain"
            )
            p.file(
                path="/tmp/hyperledger",
                state="absent",
                display_name="Delete hyperledger installation directory"
            )
            p.file(
                path="/tmp/crypto-config",
                state="absent",
                display_name="Delete crypto-config directory"
            )
            p.file(
                path="/bin/cryptogen",
                state="absent",
                display_name="Delete cryptogen"
            )

    def backup(self):
        super()
        pass
