# BTCMark
A tool for blockchain benchmarking. BCTMark can run existing experiments and how developers/scientists can integrate new blockchain systems to be tested. 

# [Tech Stack](teck_stack.md#tick-tech-stack)

# Source
This repository is a fork from https://gitlab.inria.fr/dsaingre/bctmark
The BCTMark tool is presented and used in Dimitri Saingres's thesis "Understanding the energy consumption of blockchain technologies: a focus on smart contracts". Distributed, Parallel, and Cluster Computing [cs.DC]. Ecole nationale supérieure Mines- Télécom Atlantique, 2021. English. NNT: 2021IMTA0280. tel-03546651

# Usage
<img width="655" alt="image" src="https://github.com/user-attachments/assets/a4ca093a-847c-425c-b7cc-a8400b175d27">

## Claim
The first step is to claim resources on which to deploy the experiment. BCTMark is intended to be portable to manage repeatable experiments. Experiments can be deployed on any infrastructure that supports SSH connections. Some research testbeds (like Grid’5000) require users to book resources before using them. This reservation phase can be addressed by BCTMark. As shown in Listing 4.1, the deployment topology can be described in a YAML file. This provided example can be used to deploy on a local device 1) an Ethereum network with one bootnode and two peers, 2) one benchmark worker (used to generate loads), 3) a "dashboard" server that hosts both the monitoring stack and the load generator master (that coordinate workers, see subsection 4.3.2 of the Thesis for details on load generation). In this case, the claim phase will only start with the required virtual machines. 

Bootnodes are peers that have an address known by everyone in the network. New peers can connect to those bootnodes to get the address of other peers in the network.


``` yaml
Listing 4.1 – Configuration example for local deployment with Vagrant
deployment:
vagrant:
  backend: virtualbox
  box: generic/debian10
resources:
machines:
  - roles: ["dashboard"]
    flavour: tiny
number: 1
- roles: ["ethgethclique:bootnode"]
  flavour: tiny
number: 1
- roles: ["ethgethclique:peer"]
  flavour: tiny
number: 2
- roles: ["bench_worker"]
  flavour: tiny
number: 1
```


## Prepare deployment
Once the infrastructure resources are claimed, BCTMark can prepare the experiment by deploying the required components (i.e., download and install dependencies, copy configuration files...). For each role (see Listing 4.1 in the Thesis), there is a corresponding component to be deployed. The monitoring stack (dashboard role) and the benchmarking workers (bench_worker role) are common to many experiments. Users can define their roles to deploy their blockchain network. In the example in Listing 4.1, we need two roles to deploy an Ethereum network: bootnodes 4 and peers.

## Benchmark / Replay
After deployment, users can run the benchmark themselves. BCTMark provides two possibilities to do this: an ad hoc load generation and one based on previous traces (for more details on the implementation choices, readers may refer to subsection 4.3.2 of the Thesis). Once the benchmark has ran, the results can be backed-up, and the environment destroyed/- cleaned for another experiment.

## Development and integration
From a developer’s point of view, all the following necessary actions must be implemented to integrate a new blockchain to be tested:
- Deployment: write a new Ansible playbook (cf. subsection 4.3.2) that specifies how to deploy, backup, and delete the system;
- Metric collection: write a Telegraf plugin (cf. subsection 4.3.2) to gather system-specific metrics (e.g., block emission rate) if not already available through HTTP web services (BCTMark can collect metrics exposed at a given HTTP endpoint);
- Adhoc Load generation: write functions that correspond to an interaction one can have with the system (e.g., how to send a transaction, how to call a smart contract, ...);
- Reproducible Load generation: implement functions to backup transactions (and serialize those) and functions to replay a given serialized transaction.

A developer or researcher would benefit from the design of BCTMark as a framework to easily integrate its new blockchain technology to be tested. Indeed, BCTMark already provides:
- Deployment: portability of deployment on several testbeds that support SSH;
- Network emulation: latency, bandwidth limits, ...;
- Metric collection: a collection of metrics related to the infrastructure (e.g., CPU usage);
- Load generation: distribution of the load to generate among workers.

Only specific interactions with the blockchain to be tested need to be implemented.

# Architecture
<img width="662" alt="image" src="https://github.com/user-attachments/assets/f16ab152-3f98-485f-a044-e1262594dc65">

To avoid reinventing the wheel, BCTMark is based on state-of-the-art, industry-proven tools. Altogether they empower researchers, allowing them to provision computing resources, deploy blockchain peers, generate load (based on a history to reproduce or according to a given scenario), and collect metrics relating to peers’ performance and energy consumption. The architecture of BCTMark is illustrated in Figure 4.2.

## Deployment
BCTMark can deploy the entire experiment stack: system under test, monitoring system, and load generators.

Deployment does not require any agent installation on the machines. They are managed through SSH. A playbook defines the configuration to be deployed, which takes the form of configuration files in YAML format. Those configuration files make it possible to specify the desired deployment in an explicit, documented, and repeatable way. BCT- Mark also provides an abstraction layer of the underlying infrastructure. The deployment topology can be described from a high-level point of view, portable on different testbeds. That makes experiments portable on various infrastructures such as Vagrant (local deployment), Grid’5000, and Chameleon.

To manage deployment, BCTMark uses EnosLib [31] (an open-source library to build experimental frameworks) and Ansible [1] (a software that allows managing deployment of configuration on a cluster). These two components enable self-describing, reproducible deployments.

## Metrics management
Metrics about the server (CPU, memory consumption, HDD usage, ...) and blockchains (number of blocks produced, hashrate, ...) are collected, stored in time-series and displayed by Telegraf [107], InfluxDB [52] and Grafana [48].
Telegraf natively allows the collection of server metrics through many plugins written in the Go programming language. New ones can be developed to manage the collection of data on deployed blockchain peers. Current experiments on Ethereum deployment use the HTTP plugin from Telegraf to collect metrics through the Ethereum HTTP API.

## Network Emulation
One strength of BCTMark is its ability to describe simply the desired network to emulate. Users can describe in the YAML deployment configuration file several groups of peers and emulate any desired network condition between them. The current characteristics of the network that can be emulated are the percentage of packet loss, network delay, and network rate (i.e., bandwidth). A use case of this feature could be to study the effect of a sudden network partitioning or merge on a blockchain system. Under the hood, BCTMark uses EnosLib which applies the desired network rules using the Linux command TC.

## Load generation
BCTMark supports two ways to generate workloads (By workload, we mean transactions to be processed by the system under test): an ad hoc load generation (based on Python scripts) and a load generation based on history. The first one uses Locust [64], a load generator written in Python. The user needs to specify, through Python methods, any interaction a user can have with the system under test (e.g., sending a transaction to someone or deploying/calling a smart contract). Locust will then use those methods to generate random loads.

The second way to generate load is based on a provided history. BCTMark can extract the history of a peer in the system and serialize it in a YAML file containing all the transactions. To reproduce the history, it can split the transactions between different workers, create the number of accounts needed to replay it, and let the workers re-run the transactions. This way, we can aim to replay transactions issued from the mainnet of a targeted blockchain system.

## Energy consumption
BCTMark does not embed any energy monitoring tools. However, as it enables the deployment of experiments on any kind of testbeds, it can be used to deploy systems on clusters where the energy consumption is monitored. We have already tried this by deploying experiments on the SeDuCe [82] cluster (see subsection 4.4.1). It is part of the Grid’5000 testbed and is monitored with both energy and thermal sensors.

# Validation experiments
In this section, we illustrate BCTMark’s capabilities through three experiments. The first one demonstrates its capacity to deploy experiments on different testbeds, the second one is its capacity to compare two blockchain systems, and the third one, is its usage for smart contract performance evaluation. Those experiments use two different testbeds (both having power measuring capacities):
1. A Raspberry-pi 3+ cluster. Each node has a quadcore Cortex-A53 ARMv7 CPU and 1GB of RAM.
2. Grid’5000 [5] Ecotype: A Dell PowerEdge R630 cluster. Each node has two Intel Xeon E5-2630L v4 (Broadwell, 1.80GHz, 10 cores/CPU) CPU and 128 GiB of RAM. Grid’5000 is a large-scale public research testbed containing several clusters. Ecotype is one of those clusters, located in Nantes (France).

We evaluated three blockchain systems:
1. Ethereum Ethash, an implementation of the Proof of Work (PoW) system of Ethereum. It is the default implementation of Ethereum, used in the context of a public blockchain. In this system, every peer can actively participate in block mining.
2. Ethereum Clique, an implementation of the Proof of Authority (PoA) system of Ethereum. PoA is used in the context of a private blockchain. In this system, preselected and identified peers can validate blocks one at a time. It does not involve any mining.
3. Hyperledger Fabric. It is also intended for private blockchains. Peers submit transactions to special peers called orderers. Orderers are in charge of the ordering process of transactions. Hyperledger Fabric uses a voting-based consensus protocol.

## Deployment of blockchains on two different testbeds
This experiment illustrates the capabilities of BCTMark to deploy blockchains on different testbeds. We have deployed the Ethereum Clique on both Raspberry Pi and Ecotype clusters under three scenarios. The IDLE scenario does not include any load generation. Peers just generate and share empty blocks. The two other scenarios include a load generation of 5 and 50 transactions per second. Load is generated by separated workers and spread randomly across peers. For both experiments, we deployed 12 peers and 6 load generator workers.
Results are presented in Figure 4.3. The bar plotted on the graph corresponds to the average power usage of every machines in the cluster. The error bar illustrates the standard deviation of power usage.

Those two platforms have different power draws. Power usage on the Dell servers goes from 130.4 to 131.54 watts (0.7% increase) whereas power usage on the Raspberry Pi platform goes from 3.4 to 5.2 watts (44% increase). This result was expected as Raspberry Pi is much more limited than classical "high performances" Dell servers. This experiment however illustrates that non-mining chains can be installed on low-power platforms like Raspberry Pi. This can be useful in the context of the development of blockchains in IoT / Edge computing. In the context of research on energy consumption, low-power platforms can be useful to illustrate subtle differences in consumption.
We can, however, note that this conclusion may not be the same for mining systems such as Ethereum Ethash. Indeed, we could not install Ethash on our Raspberry Pi platform due to a shortage of memory. The algorithm used by Ethereum Ethash for mining is memory intensive and therefore not suited for low-power platforms with not enough RAM. A solution for this issue could be to set-up both high-performance nodes dedicated to mining and low-power nodes that would only broadcast transactions to the miner’s network.

<img width="507" alt="image" src="https://github.com/user-attachments/assets/1fa3e10d-864c-41a9-99f1-1bc1685f8bc3">

4.4.2 Comparison of CPU usage of three blockchain systems
This experiment aims to illustrate the capabilities of BCTMark to deploy different blockchain systems. We deployed Hyperledger Fabric, Ethereum Ethash, and Ethereum Clique on the Ecotype cluster under four scenarios: IDLE (no-load generation) and load generation of 5, 50, and 200 transactions per second. The deployed network is composed of a network of 39 peers and three load generator workers. Figure 4.4 illustrates this experiment. The bar corresponds to the average CPU usage across all machines, whereas the error bar goes from the 10th quartile to the 90th quartile.
We can first notice that the CPU consumption of the Ethash system exceeds the CPU usage of the two others. Moreover, in this deployment, peers only mine blocks using one thread. It could be possible to dedicate more resources for mining, increasing the CPU consumption furthermore. The other two systems have non-mining consensus systems, decreasing the amount of computation needed to secure the network.
The CPU usage of non-mining systems is also more stable than the Ethash system. Figure 4.5 illustrates the evolution of the CPU usage for Ethash peers during the "200 transactions per second" scenario. (CPU usage values seem to differ from the ones in Figure 4.4 but this visual effect is due to 1) high variance in data and 2) high density in data points that hides the lowest values. We can notice the high variance in Figure 4.4.) The spike at the beginning of the experiment, reaching almost 100% CPU, is due to the construction of the data structure needed by peers to start mining. We can also see that, after this spike, the CPU usage increases over time. This increase may be due to the evolution of the difficulty in mining resulting from the mining competition between peers.
On the other hand, in the first three scenarios, the CPU consumption of the two private blockchains is roughly the same. However, at 200 transactions per second, the CPU consumption of the Ethereum Clique network increases from 0.3% to 2.9%. This increase suggests that Hyperledger Fabric could have better performances in the context of a private blockchain. These results about private blockchains are consistent with those shown in the Blockbench. paper [22].

<img width="516" alt="image" src="https://github.com/user-attachments/assets/2b74b98d-4638-4f3a-bdf9-20cfd5b501ab">
<img width="516" alt="image" src="https://github.com/user-attachments/assets/804e2bf0-ce23-4302-ae33-cb20b612798e">

## Experiments Reproducibility
One of the goals behind BCTMark was to enforce reproducibility in blockchain experiments. Reproducibility means that running experiments several times (in similar conditions) should give coherent results. The goal of this section is to illustrate how experiments made with BCTMark can be reproduced.
We reproduced the experiments done in subsection 4.4.2 on Ethereum Clique and Ethash to have data on both public and private blockchain systems (readers can refer to this section to read about the infrastructure used and the deployment topology). Each of the four scenarios has been run six times. For every run, we have recorded the average CPU usage across all machines. The data presented in Table 4.2 illustrate the differences in the results we obtained. For instance, the min column illustrates the min CPU average across the six runs. Experiments should show consistent results to be considered reproducible.
These results show that we obtained few differences between the six runs. The standard deviation (column ’Std’) remains low across all scenarios. This small difference in results leads us to believe that experiments with BCTMark should produce consistent results. Having exactly the same deployment topology with the same configuration is, in our opinion, the main factor explaining these consistent results. BCTMark allows researchers to share experiments that can be run in the same way by other peers in their community.

<img width="465" alt="image" src="https://github.com/user-attachments/assets/78ff37d4-211a-4082-a60c-272834933acb">




