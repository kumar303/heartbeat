A Raspberry Pi heartbeat
========================

This sends dstat pings from a Raspbery Pi box to a central server for analysis.

This requires Python 2.7

Install::

    sudo apt-get update
    sudo apt-get install dstat python-pip
    cd heartbeat
    sudo pip install -r requirements/prod.txt
    sudo python setup.py develop

Run::

    heartbeat

You need a heartbeat server which is still in the works.

Test it locally::

    pip install -r requirements/test.txt
    nosetests
