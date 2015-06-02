# Change Log
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## 0.0.6 - [unreleased]
### Added
* Volumes declared on test containers can now be cached between calls by using
  the `--cache` flag (cached in your user's cache folder)
* Support for creating inventory groups in the test file
* Failed tests are now committed so that they can be inspected by the user (can
  be disabled by using the `--no-save-failed` flag)

### Changed
* `centos` images now have some extra packages installed to make them closer
  to a normal instance
* Docker version is detected by the API at start

### Fixed
* Prevent `make docker` from picking up `docker/Makefile` as a target.
* Bug when trying to load an ansible-galaxy role with `--roles-path` not set (again)
* Properly count failed and successful tests
* Crash when `Dead` is not returned by the inspect API

## [0.0.5] - 2015-05-22
### Changed
* Flags now override the config, so it is possible to so things such as
  `-c config.yml --roles-path=/path/to/roles` and have the --roles-path
  override the config

### Fixed
* A bug when not all paths are specified when a config file is used

## [0.0.4] - 2015-05-22
### Added
* Pull images that are not available locally during tests
* New docker-pull target in the Makefile
* New `--config flag` to provide preconfigured role, library and plugin folders

### Changed
* Can customize the virtualenv binary in the Makefile
* Bindings on the ansible box are now read-only
* Merge all docker Makefiles in a single one

### Fixed
* Use a temporary dir in the user path (boot2docker support)
* Annoying log output on osx about urllib

## [0.0.3] - 2015-05-20
### Added
* Added changelog
* Python 3.x support using six

### Changed
* Cleaned up Makefile
* Added some extra data in setup.py

### Fixed
* Fixed duplicate @click.command in cli.py

## [0.0.2] - 2015-05-18
### Added
* Added docker images on docker registry
* Added `--privileged` option

### Changed
* Cleaned up README
* Better option documentation
* Containers are not started in privileged mode anymore
* Changed httpredir mirror for debian to cloudfront mirror

### Fixed
* Bug when trying to load an ansible-galaxy role with `--roles-path` not set
* Added dbus to centos:7 image
* Fixed resolvconf package on debian

## [0.0.1] - 2015-05-15
### Added
* Initial version

[unreleased]: https://github.com/AerisCloud/ansible-role-test/compare/v0.0.5...HEAD
[0.0.5]: https://github.com/AerisCloud/ansible-role-test/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/AerisCloud/ansible-role-test/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/AerisCloud/ansible-role-test/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/AerisCloud/ansible-role-test/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/AerisCloud/ansible-role-test/tree/v0.0.1
