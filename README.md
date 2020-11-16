# rossum

[![PyPI - version](https://img.shields.io/pypi/v/rossum.svg)](https://pypi.python.org/pypi/rossum)
[![Build Status](https://travis-ci.com/rossumai/rossum.svg?branch=master)](https://travis-ci.com/rossumai/rossum)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![codecov](https://codecov.io/gh/rossumai/rossum/branch/master/graph/badge.svg)](https://codecov.io/gh/rossumai/rossum)
![PyPI - supported python versions](https://img.shields.io/pypi/pyversions/rossum.svg)
![MIT licence](https://img.shields.io/pypi/l/rossum.svg)

```
The elisctl package has been renamed to rossum.
You may want to uninstall elisctl before installing rossum.
```

**rossum** is a set of [tools for Rossum integrators](https://developers.rossum.ai/) that wrap
the [Rossum API](https://api.elis.rossum.ai/docs)
to provide an easy way to configure and customize a Rossum account - either
interactively or programmatically.

## Installation

See the [rossum setup tutorial](https://developers.rossum.ai/docs/setting-up-rossum-tool)
for detailed instructions.

### Windows

Download an installation file from
[GitHub releases](https://github.com/rossumai/rossum/releases).
Install it. And run it either from start menu or from command prompt.

### UNIX based systems

Install the package from PyPI:
```bash
pip install rossum
```

## Usage
### Python API Client Library
The **rossum** library can be used to communicate with Rossum API,
instead of using `requests` library directly. The advantages of using **rossum**:
* it contains a function that merges the paginated results into one list so the user does not need
to get results page by page and take care of their merging,
* it takes care of login and logout for the user,
* in case the API version changes, the change will be implemented to the
library by Rossum for all the users.

See the sample script using **rossum** within a code to export the documents:

```python
import json
import logging

from rossum.lib.api_client import APIClient
from datetime import date, timedelta

queue_id = 12673
username = 'your_username'
password = 'your_password'
reviewed_documents = "exported,exporting,failed_export"

# This example downloads data for documents exported during the previous calendar day.
date_today = date.today()
date_end = date_today
date_start = date_today - timedelta(days=1)

def export_documents():
    logging.info("Export started...")
    with APIClient(context=None, user=username, password=password) as rossum:

            annotations_list, _ = rossum.get_paginated(f"queues/{queue_id}/export",
                                                        {"status": reviewed_documents,
                                                        "format": "json",
                                                        "ordering": "exported_at",
                                                        "exported_at_after": date_start.isoformat(),
                                                        "exported_at_before": date_end.isoformat()})

            with open('data.json', 'w') as f:
                json.dump(annotations_list, f)
    logging.info("...export finished.")

if __name__ == "__main__":
    export_documents()

```
### API Client command line tool
The **rossum** tool can be either used in a **command line interface** mode
by executing each command through `rossum` individually by passing it as an argument,
or in an **interactive shell** mode of executing `rossum` without parameters
and then typing the commands into the shown prompt.

Individual Rossum operations are triggered by passing specific *commands* to `rossum`.
Commands are organized by object type in a tree-like structure and thus are composed
of multiple words (e.g. `user create` or `schema transform`).

So either get the list of commands and execute them immediately such as:
```shell
$ rossum --help
$ rossum configure
```
or run the interactive shell by simply running
```shell
$ rossum
```
See the sample using **rossum** command line tool to create the main objects within an organization and  
assign a user to a queue:
```shell
$ rossum configure
API URL [https://api.elis.rossum.ai]:
Username: your_username@company.com
Password:
$ rossum workspace create "My New Workspace"
12345
$ rossum queue create "My New Queue Via rossum" -s schema.json -w 12345 --email-prefix my-queue-email --bounce-email bounced-docs-here@company.com
50117, my-queue-email-ccddc6@elis.rossum.ai
$ rossum user create john.doe@company.com -q 50117 -g annotator -p my-secret-password-154568
59119, my-secret-password-154568
$ rossum user_assignment add -u 59119 -q 50117
```

## Configure profiles

To run commands described below under a chosen user, it is possible to use profiles defined by
configure function such as
```shell
$ rossum --profile profile_name configure
```

After defining necessary profiles and their credentials, the profile can be chosen the following way
```shell
$ rossum --profile profile_name queue list
```

## Edit Schema

Some of the most common advanced operations are related to setting up
the sidebar-describing schema according to business requirements. Using rossum
you can edit schema easily as a JSON or XLSX file.

List queues to obtain schema id:
```shell
$ rossum queue list
  id  name                           workspace  inbox                                       schema  users
----  ---------------------------  -----------  ----------------------------------------  --------  ----------------------
   6  My Queue 1                             6  myqueue-ab12ee@elis.rossum.ai                    7  27
```

Download schema as a json:
```shell
$ rossum schema get 7 -O schema.json
```

Open the `schema.json` file in you favourite editor and upload modified version back to Rossum.
```shell
$ rossum schema update 7 --rewrite schema.json
```

You can also edit schema as an Excel (xlsx) file.
```shell
$ rossum schema get 7 --format xlsx -O schema.xlsx
$ rossum schema update 7 --rewrite schema.xlsx
```

From now on, documents will follow new schema. (Warning! If you don't use `--rewrite` option,
the new schema will receive a new id - obtain it by `queue list` again.)


## Schema Transformations

In addition, there is a scripting support for many common schema operations,
that may be easily used for schema management automation. See `rossum schema transform`
and `rossum tools` tools for further reference.

Run something like:
```shell
$ rossum schema transform substitute-options default_schema.json centre <( \
   rossum tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 --sheet 1 | rossum tools csv_to_options - ) \
 | rossum schema transform substitute-options - gl_code <( \
    rossum tools xls_to_csv ~/Downloads/ERA_osnova_strediska.xlsx --header 0 | rossum tools csv_to_options - ) \
 | rossum schema transform remove - contract \
 > era_schema.json
```

## License
MIT

## Contributing

* Use [`pre-commit`](https://pre-commit.com/#install) to avoid linting issues.
* Submit a pull request from forked version of this repo.
* Select any of the maintainers as a reviewer.
* After an approved review, when releasing, a `Collaborator` with `Admin` role shall run in `master` branch:
    ```bash
    bump2version minor
    git push
    git push --tags
    ``` 
* To build a Windows installer, run:
    ```bash
    pynsist installer.cfg
    ``` 
   
## Changelog
### 2020-11-16 v3.4.0
* Create password command

### 2020-11-11 v3.3.0
* Allow passing parameters when listing hooks
* Fix passing metadata when creating a workspace

### 2020-10-20 v3.2.1
* Remove Obsoletes-Dist

### 2020-10-20 v3.2.0
* Enable creating serverless functions
* Add method for creating workspaces
* Allow setting up sideloading on hooks
* Refactor _request_url() to allow custom logging

### 2020-09-29 v3.1.0
* Fix missing library in setup.py
* Remove references to old package names
* Update `setup.py`

### 2020-09-29 v3.0.0
* elisctl was renamed to rossum

### 2020-07-27 v2.10.1
* Fix attribute name for setting max token lifetime

### 2020-07-24 v2.10.0
* Add `schema list` command
* Fix `webhook change` command issue
* Remove `csv get` command
* Add example script for setting up a new organisation
* Enable assigning manager role to user
* Enable setting max token lifetime
* Catch ValueError when parsing schema in XLSX
* Fix Python3.8 support

### 2020-02-18 v2.9.0
* allow editing inbox attributes separately on queue-related commands
* add support for `can_collapse` in xlsx schema
* add sample usage of elisctl library in a Python code
* make queue option required on `user create`

### 2019-10-31 v2.8.0
* Add webhook command
* Allow creating and changing inbox properties on `queue change` command

### 2019-09-30 v2.7.1
* Improve documentation

### 2019-08-13 v2.7.0
* Add command `user_assignment` for bulk assignment of users to queues
* Change command `connector create`: `queue_id` parameter needs to be specified, if there is more than one queue in organization
* Support schema attribute `width` in XLSX schema format
* Fixed: booleans, in XLSX schema format, can be specified as boolean types
* Internal: filename can be specified in `ELISClient.upload_document`


### 2019-07-30 v2.6.0
* Enable passing custom filename with upload

### 2019-07-12 v2.5.0

* Add support for schema specified in XLSX when creating queue
* Remove the necessity to specify schema file type when uploading
* Fix XML and CSV formats of `elisctl document extract`

### 2019-07-09 v2.4.0

* Add support for can_export in xlsx schema format
* Add document command

### 2019-06-21 v2.3.1

* Fix: annotator cannot use `elisctl connector list` command

### 2019-06-13 v2.3.0

* Add connector command

### 2019-06-11 v2.2.1

* Update packages for windows build.


### 2019-06-03 v2.2.0

* Added support for [`--profile`](#configure-profiles) option to all `elisctl` commands
* Fix: remove extra whitespace in xlsx schema export/import

### 2019-04-02 v2.1.0

* Added support for `--output-file` to `elisctl tools` and `elisctl schema transform`
* Fix [Schema Transformations](#schema-transformations) description in README

### 2019-03-14 v2.0.1

* Fixed MS Windows application entry point (running elisctl from the start menu)
* Fixed parsing of boolean values in xlsx schema export/import

### 2019-03-14 v2.0.0

* Disable interpolation in config parsing, so that special characters are allowed in e.g. password
* Experimental support for schema modification using xlsx file format
* Allow to show help in schema transform add (backward incompatible change)

### 2019-03-08 v1.1.1

* Fixed bug with UnicodeDecodeError in `elisctl schema get ID -O file.json` on Windows

### 2019-03-03 v1.1.0

* Added support for python 3.6
* Added `User-Agent` header (`elisctl/{version} ({platform})`) for every request to ROSSUM API
* Improved error when login fails with the provided credentials
