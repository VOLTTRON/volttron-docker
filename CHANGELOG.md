# Changelog

## [v3.2](https://github.com/VOLTTRON/volttron-docker/tree/v3.2)  (2022-02-28)

[Full Changelog](https://github.com/VOLTTRON/volttron-docker/compare/v3.1...HEAD)

**Closed issues:**

- Error on ZMQ socket bind\(\) needs more information, patch attached. [\#63](https://github.com/VOLTTRON/volttron-docker/issues/63)
- Volttron1 container is not reentrant [\#54](https://github.com/VOLTTRON/volttron-docker/issues/54)
- realpath not a thing anymore [\#11](https://github.com/VOLTTRON/volttron-docker/issues/11)

**Merged pull requests:**

- Fix reentrant bug [\#62](https://github.com/VOLTTRON/volttron-docker/pull/62) ([bonicim](https://github.com/bonicim))
- Merge release/v3.1 into main [\#61](https://github.com/VOLTTRON/volttron-docker/pull/61) ([github-actions[bot]](https://github.com/apps/github-actions))
- Update Workflows and README [\#58](https://github.com/VOLTTRON/volttron-docker/pull/58) ([bonicim](https://github.com/bonicim))
- Fix docker-compose script and platform config for Volttron Central agent [\#52](https://github.com/VOLTTRON/volttron-docker/pull/52) ([bonicim](https://github.com/bonicim))

## [v3.1](https://github.com/VOLTTRON/volttron-docker/tree/v3.1) (2022-01-14)

[Full Changelog](https://github.com/VOLTTRON/volttron-docker/compare/v3.0...v3.1)

**Closed issues:**

- VOLTTRON Central Agent Showing status of 1 [\#48](https://github.com/VOLTTRON/volttron-docker/issues/48)

**Merged pull requests:**

- Pin volttron submodule to 8.1.3 [\#59](https://github.com/VOLTTRON/volttron-docker/pull/59) ([bonicim](https://github.com/bonicim))
- Add DockerHub README and supporting Workflow action [\#57](https://github.com/VOLTTRON/volttron-docker/pull/57) ([bonicim](https://github.com/bonicim))
- Automate release process for Volttron Docker image [\#56](https://github.com/VOLTTRON/volttron-docker/pull/56) ([bonicim](https://github.com/bonicim))
- Remove Python 3.6, add \>=3.7 to all GH workflows [\#53](https://github.com/VOLTTRON/volttron-docker/pull/53) ([bonicim](https://github.com/bonicim))
- Update platform\_config.yml config for VolttronCentral [\#51](https://github.com/VOLTTRON/volttron-docker/pull/51) ([bonicim](https://github.com/bonicim))

## [v3.0](https://github.com/VOLTTRON/volttron-docker/tree/v3.0) (2021-12-09)

[Full Changelog](https://github.com/VOLTTRON/volttron-docker/compare/v2.0...v3.0)

**Merged pull requests:**

- Release/3.0 [\#50](https://github.com/VOLTTRON/volttron-docker/pull/50) ([bonicim](https://github.com/bonicim))
- Pin Volttron to 8.x; update README and docker-compose scripts [\#49](https://github.com/VOLTTRON/volttron-docker/pull/49) ([bonicim](https://github.com/bonicim))

## [v2.0](https://github.com/VOLTTRON/volttron-docker/tree/v2.0) (2021-11-03)

[Full Changelog](https://github.com/VOLTTRON/volttron-docker/compare/c7216d9b36c260f931bfa99054f09c27fd4b9414...v2.0)

**Closed issues:**

- Docker installation does not set proper permissions on socket [\#40](https://github.com/VOLTTRON/volttron-docker/issues/40)
- rmq certification is changed [\#27](https://github.com/VOLTTRON/volttron-docker/issues/27)
- mount host VOLTTRON\_HOME [\#25](https://github.com/VOLTTRON/volttron-docker/issues/25)
- docker-compose-rmq.yml  [\#23](https://github.com/VOLTTRON/volttron-docker/issues/23)
- Setup doesn't create the correct permissions on VOLTTRON\_HOME directory [\#9](https://github.com/VOLTTRON/volttron-docker/issues/9)
- The agent install priority in the setup-platform.py file is hard coded [\#6](https://github.com/VOLTTRON/volttron-docker/issues/6)

**Merged pull requests:**

- Release/1.0 [\#46](https://github.com/VOLTTRON/volttron-docker/pull/46) ([bonicim](https://github.com/bonicim))
- Update/8.1.1volt [\#45](https://github.com/VOLTTRON/volttron-docker/pull/45) ([bonicim](https://github.com/bonicim))
- Update Dockerfile, docker-compose files, and README [\#42](https://github.com/VOLTTRON/volttron-docker/pull/42) ([bonicim](https://github.com/bonicim))
- Updated volttron submodule to point to main branch [\#41](https://github.com/VOLTTRON/volttron-docker/pull/41) ([craig8](https://github.com/craig8))
- Merge main into develop [\#39](https://github.com/VOLTTRON/volttron-docker/pull/39) ([bonicim](https://github.com/bonicim))
- Update README instructions in Quickstart section [\#38](https://github.com/VOLTTRON/volttron-docker/pull/38) ([bonicim](https://github.com/bonicim))
- Update README [\#37](https://github.com/VOLTTRON/volttron-docker/pull/37) ([bonicim](https://github.com/bonicim))
- Develop [\#36](https://github.com/VOLTTRON/volttron-docker/pull/36) ([bonicim](https://github.com/bonicim))
- Fix setup-platform.py to not fail on agent installation [\#35](https://github.com/VOLTTRON/volttron-docker/pull/35) ([bonicim](https://github.com/bonicim))
- chore: update readme [\#33](https://github.com/VOLTTRON/volttron-docker/pull/33) ([timothyclifford](https://github.com/timothyclifford))
- Merge release branch, Release 1.0, into develop [\#32](https://github.com/VOLTTRON/volttron-docker/pull/32) ([bonicim](https://github.com/bonicim))
- Merge release branch, Release 1.0, into main [\#31](https://github.com/VOLTTRON/volttron-docker/pull/31) ([bonicim](https://github.com/bonicim))
- fix \#27 \(rmq certification is changed\) [\#29](https://github.com/VOLTTRON/volttron-docker/pull/29) ([GHYOON](https://github.com/GHYOON))
- Fix web ssl issue [\#26](https://github.com/VOLTTRON/volttron-docker/pull/26) ([GHYOON](https://github.com/GHYOON))
- Add docker image test scripts and Github Actions Workflows [\#22](https://github.com/VOLTTRON/volttron-docker/pull/22) ([bonicim](https://github.com/bonicim))
- Revert "Revert "Add docker image test scripts c2"" [\#19](https://github.com/VOLTTRON/volttron-docker/pull/19) ([bonicim](https://github.com/bonicim))
- Revert "Add docker image test scripts c2" [\#18](https://github.com/VOLTTRON/volttron-docker/pull/18) ([bonicim](https://github.com/bonicim))
- Add docker image test scripts c2 [\#17](https://github.com/VOLTTRON/volttron-docker/pull/17) ([bonicim](https://github.com/bonicim))
- Update Docker image for rmq and zmq [\#15](https://github.com/VOLTTRON/volttron-docker/pull/15) ([bonicim](https://github.com/bonicim))
- Modified to recursively change the owner of the volttron home [\#14](https://github.com/VOLTTRON/volttron-docker/pull/14) ([craig8](https://github.com/craig8))
- Fix bugs in setup-platform; update platform\_config and volttron submodule [\#13](https://github.com/VOLTTRON/volttron-docker/pull/13) ([bonicim](https://github.com/bonicim))
- Fix bootstart script; add symlink in Dockerfile [\#12](https://github.com/VOLTTRON/volttron-docker/pull/12) ([bonicim](https://github.com/bonicim))
- Handle permission issue as USER\_ID shouldn't be hard coded. [\#10](https://github.com/VOLTTRON/volttron-docker/pull/10) ([craig8](https://github.com/craig8))
- system now builds with python3 and volttron7 release candidate [\#8](https://github.com/VOLTTRON/volttron-docker/pull/8) ([laroque](https://github.com/laroque))
- Added code for getting agent install priority from the system config … [\#7](https://github.com/VOLTTRON/volttron-docker/pull/7) ([dzimmanck](https://github.com/dzimmanck))
- multi-architecture build automation on travis [\#5](https://github.com/VOLTTRON/volttron-docker/pull/5) ([laroque](https://github.com/laroque))
- merge of updated docker-compose based on fuel-cells example [\#4](https://github.com/VOLTTRON/volttron-docker/pull/4) ([laroque](https://github.com/laroque))
- handled existing certs use case [\#3](https://github.com/VOLTTRON/volttron-docker/pull/3) ([schandrika](https://github.com/schandrika))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
