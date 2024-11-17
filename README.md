[![Mastodon](https://img.shields.io/mastodon/follow/110779442452085429?domain=https%3A%2F%2Finfosec.exchange&style=flat-square&logo=mastodon&logoColor=fff)](https://infosec.exchange/@honoki)
[![BlueSky](https://img.shields.io/badge/@honoki.net-0285FA?logo=bluesky&logoColor=fff&style=flat-square)](https://bsky.app/profile/honoki.net)

## bbrf-agents

The Bug Bounty Reconnaissance Framework (BBRF) can be used to facilitate the workflows of security researchers across multiple devices.

This repository contains a set of lambda functions (agents) that can be deployed to AWS Lambda with [the serverless framework](https://serverless.com/).

When these agents are successfully deployed, you can run them with BBRF as follows:

```bash
# run the crtmonitor agent for the active program
bbrf run crtmonitor 

# run securitytrails for program "example"
bbrf run securitytrails -p example
```

Learn more:
* BBRF client: https://github.com/honoki/bbrf-client
* BBRF server: https://github.com/honoki/bbrf-server

### How to deploy

This set of lambdas is built on top of Serverless, and contains a [serverless.yml](serverless.yml) configuration file that should get you started in minutes:

```bash
# clone this repository
git clone https://github.com/honoki/bbrf-agents

# install the serverless framework - see https://www.serverless.com/framework/docs/getting-started/
curl -o- -L https://slss.io/install | bash

# run the serverless deploy command and follow the steps to
# get things up and running
sls deploy

# if the post-deploy function fails, you can auto-register all
# deployed agents by invoking the agent-registration-service
sls invoke -f agent-registration-service
```