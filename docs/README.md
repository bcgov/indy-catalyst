
# Hyperledger Aries VCR <!-- omit in toc -->

![logo](/docs/assets/aries-vcr-logo-bw.png)

# Table of Contents <!-- omit in toc -->

- [Introduction](##introduction)
- [Before You Start](##before-you-start)
- [Repositories](##before-you-start)
- [Prerequisites](##prerequisites)
- [Running a VON - Verified Organizations Network](##running-a-von---verified-organizations-network)
  - [Running on Docker Locally](###running-the-network-on-docker-locally)
- [Aries VCR](##aries-vcr)
  - [Building the Images](###building-the-images)
  - [Starting the Project](###starting-the-project)
  - [Stopping the Project](###stopping-the-project)
  - [Using the Application](###using-the-application)
  - [Live Web Development(Credential Registry)](###live-web-development)
  - [Start-up Orchestration](###start--up-orchestration)
- [Indy Catalyst Issuer Controller](##indy-catalyst-issuer-controller)
  - [Initialize the Project](###initialize-the-project)
  - [Register the DID](###register-the-did)
  - [Build and Start the Project](###build-and-start-the-project)
  - [Issuing Credentials](###issuing-credentials)

## Introduction

This guide is intended for use by teams and entities who are planning to or currently working with the aries-vcr software components.

If you are unfamiliar with the underpinning technologies and concepts that are utilized in this project please review the getting started documentation in the vonx.io homepage: [Get Started with VON - Verifiable Organizations Network](https:\\vonx.io\getting_started\get-started\#technical-components-of-a-von-ecosystem)

## Before you Start

Running this project in development requires a running VON - Verified Organizations Network, the aries-vcr project and an Aries VCR Issuer Controller.

Aries VCR is a cloud based project that is developed as a cloud-native application. All components are developed in Docker first. <em> As such we <b>strongly recommend</b> that using Docker for all development local or otherwise</em>.

<span style="color:red;">The aries-vcr contributors do not test or develop any of the technical components on bare metal.</span>

## Repositories

Running all components of an Aries VCR network in development requires the following repositories:

- [VON - Verified Organizations Network](https://github.com/bcgov/von-network)
- [Aries VCR](https://github.com/hyperledger/aries-vcr)
- [Indy Catalyst Issuer Controller](https://github.com/bcgov/indy-catalyst-issuer-controller)

The Issuer Controller may not be necessary for your project implementation if there is no need for issuing credentials. It will still be required for development (to issue credentials) if you do not have a separate agent that you are using for issuing.

It is recommended to fork all the listed repositories, with the exception of the Issuer Control. If your use case requires an issuer controller follow the outlined procedure in the issuer-controller guide.

## Prerequisites

- Docker and Docker Compose
  - Install and configure Docker and Docker compose for your system.

- [The S2I CLI](https://github.com/openshift/source-to-image/releases).
  - Download and install the S2I CLI tool; source-to-image
  - Running the S2I CLI tool with the manage script requires having the executable on your PATH. If it is not found you will get a message asking you to download and set it on your PATH.
- Manage Script
  - The manage script wraps the Docker and S2I process in easy to use commands.

## Running a VON - Verified Organizations Network

The following instructions provide details on how to deploy the project using Docker Compose. This method of deployment is intended for local development and demonstration purposes. It is NOT intended to be support production level deployments where security, availability, resilience, and data integrity are important.

### Running the Network On Docker Locally

Open a terminal session, change directories to where you store repos, and clone the von-network repository:
```bash
git clone <repository url> von-network
# Move to the new directory:
cd von-network
# Build the docker images that will be used to run the Indy network containers (this process will take several minutes):
./manage build
```

The `./manage` script has a number of commands. Run it without arguments to see the set of options.

Once the build process completes, you can test the build to make sure everything works properly:
`./manage start`
Monitor the logs for error messages as the nodes start up.

Verify the network is running
In a browser, go to http://localhost:9000. You should see the VON Indy Ledger Browser and the status of the four nodes of the Indy Network. All should show a lovely, complete blue circle. If not - check the logs in the terminal.

Stopping the Network
To stop the scrolling logs and get to a command prompt, hit Ctrl-C. To stop and remove the network persistence (the Ledger), run: `./manage down`
If necessary, you can use `./manage stop` instead of down to stop the containers but retain the persistence.

## Aries VCR

Fork and clone the Aries VCR project as per the initial instructions at the outset.

Fork the project, navigate to the folder where you keep your projects and repositories and run `git clone https://github.com/<username>/aries-vcr`

There are a few different technical components to the project which are described in more detail here [link]

Finally, change directory to the new created starter-kit located in the aries-vcr project folder:
`cd aries-vcr/starter-kits/credential-registry/docker`

### Building the Images

Building the images requires a combination of Docker and S2I builds the process has been scripted inside manage. 

To build the images run `./manage build`

### Starting the Project

The Aries VCR starter kit requires a unique seed for development. This is a 32 character value that uniquely identifies your wallet/ledger seed to the VON ledger running locally or on another network.

You will need to choose a unique seed value for development. Use a value that is not used by another agent within the environment. It must be 32 characters long exactly. If you're using an externally hosted VON ledger you will need to be careful to select a unique seed in this step.

Register the unique seed by running the following script command: 

`./manage registerDids seed=my_unique_seed_00000000000000000`

Finally run the manage script to start the project: 

`./manage start seed=my_unique_seed_00000000000000000`

This will start the project interactively; with all of the logs being written to the command line.

### Stopping the Project

There are two commands to stop the project. Down and Stop.

#### Stop

Stop stops the containers, but leaves the rest of the docker-compose structure in place - volumes (and the Indy wallets they store) and networking.

To stop the containers without destroying them run:

`./manage stop`

#### Down

Down is destructive, removing the volumes and network elements. Often in a debugging session, stop is sufficient. If you use down, you likely will have to restart the prerequisite Indy network.

To remove the volumes and network elements run: 

`./manage down`

### Using the Application

- The main UI is exposed at: http://localhost:8080/
- The API is exposed at: http://localhost:8081/
- Schema-Spy is exposed at: http://localhost:8082/
- Solr is exposed at: http://localhost:8983/
- The database is exposed at: http://localhost:5432/

### Live Web Development

The Aries VCR Org Book can also be brought up in a state where local modifications to the vcr-web component are detected automatically, resulting in recompilation of the Javascript and CSS resources and a page reload when viewed in a web browser. To run Aries VCR Org Book using this method execute:

`./manage web-dev seed="my_seed_000000000000000000000000"`

### Theme Development

Custom development of themes based on the Credential Registry starter kit is possible by following this [guide](../credential-registry\client\vcr-web\ThemeDevelopment.md)

### Start-up Orchestration

The API server manages the database schema and indexes, therefore it must wait until the database and search engine (Solr) services are up and running AND fully initialized. Likewise, the Schema-Spy service must wait until the API service has created\migrated the database schema to the most recent version before it starts.

To accomplish this the docker compose file defines simple sleep commands to pause the startup for these services. It would be nice to develop a more deterministic solution for the start-up orchestration. In the case of the API server it would sufficient to detect that Solr and PostgreSQL are responding, however, in the case of the Schema-Spy service this would be insufficient as the API server needs time to create or migrate the schema to the latest version before Schema-Spy starts.

## Indy Catalyst Issuer Controller

There are two issuer-verifier agents that are available for use with your project. The simplified issuer controller recommended for quick-start is the [Indy Catalyst Issuer Controller](https://github.com/bcgov/indy-catalyst-issuer-controller/blob/master/GettingStartedTutorial.md#von-agent-getting-started-tutorial)

### Initialize the project

Clone the project into your projects folder, or if you are creating an issuer controller for use as a custom issuer-verifier as part of your project rather than just for testing purposes start a new github project, download the code, and copy it into a local clone of the github project.

Run the initialization script after cloning the project.

```bash
# Start in the folder with repos (Local Machine) or home directory (In Browser)
$ cd indy-catalyst-issuer-controller
$ . init.sh  # And follow the prompts
```

The init.sh script does a number of things:

- Prompts for some names to use for your basic agent.
- Prompts for whether you are running with Play With Docker or locally and sets some variables accordingly.
- Shows you the lines that were changed in the agent configuration files (in issuer_controller/config).

### Register the DID

This project does not currently automatically register the DID located in the settings.yml file.

The DID is located in the `indy-catalyst-issuer-controller/docker/manage` file on line 105 (it will default to myorg_issuer_0000000000000000001)

### Build and Start the Project

Navigate to the docker folder in the project. Run: `./manage build` to build all the necessary containers.
Finally run `./manage start` to initialize the project.

### Issuing Credentials

There are a couple of different ways to issue credentials in the agent issuer. Review the full documentation located here to learn more about the agent issuer located [here](https://github.com/bcgov/indy-catalyst-issuer-controller).

To submit credentials, use Postman (or similar, based on your local configuration) to submit the following to http://localhost:5000/issue-credential
```
[
    {
        "schema": "ian-registration.ian-ville",
        "version": "1.0.0",
        "attributes": {
            "corp_num": "ABC12345",
            "registration_date": "2018-01-01", 
            "entity_name": "Ima Permit",
            "entity_name_effective": "2018-01-01", 
            "entity_status": "ACT", 
            "entity_status_effective": "2019-01-01",
            "entity_type": "ABC", 
            "registered_jurisdiction": "BC", 
            "addressee": "A Person",
            "address_line_1": "123 Some Street",
            "city": "Victoria",
            "country": "Canada",
            "postal_code": "V1V1V1",
            "province": "BC",
            "effective_date": "2019-01-01",
            "expiry_date": ""
        }
    },
    {
        "schema": "ian-permit.ian-ville",
        "version": "1.0.0",
        "attributes": {
            "permit_id": "MYPERMIT12345",
            "entity_name": "Ima Permit",
            "corp_num": "ABC12345",
            "permit_issued_date": "2018-01-01", 
            "permit_type": "ABC", 
            "permit_status": "OK", 
            "effective_date": "2019-01-01"
        }
    }
]
```