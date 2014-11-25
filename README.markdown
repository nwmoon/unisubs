This repository is the code for the [Amara](http://amara.org) project.

The full documentation can be found at
http://amara.readthedocs.org/en/latest/index.html

[Amara]: http://amara.org

Quick Start
-----------

Amara uses [Docker](http://docker.io).  For ease of development, we use the [Fig](http://orchardup.github.io/fig/) tool to have a full, production like, local dev environment.

1. Git clone the repository:

        git clone git://github.com/pculture/unisubs.git unisubs

   Now the entire project will be in the unisubs directory.

2. Install Fig (http://orchardup.github.io/fig/install.html)

3. Build the Amara docker image:

        ./bin/dev build

4. Start Amara Services:

        fig up -d db worker cache search queue

5. Configure Database:

        ./bin/dev dbreset

6. Start Amara:

        fig up app

7. Add `unisubs.example.com` to your hosts file, pointing at `127.0.0.1`.  This
   is necessary for Twitter and Facebook oauth to work correctly.

   You can access the site at <http://unisubs.example.com:8000>.

To see services logs, run `fig logs <service>` i.e. `fig logs worker`

Testing
-------

To run the test suite:

        ./bin/test.sh


Dev Notes
---------

To run a single `manage.py` command:

        fig run --rm app python manage.py <command>

To see running services:

        fig ps

To stop and remove all containers:

        fig kill ; fig rm

To view logs from a service:

        fig logs <service>

To create an admin user:

        fig run --rm app python manage.py createsuperuser --settings=dev_settings
