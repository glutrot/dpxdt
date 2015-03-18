#!/usr/bin/env python
# Copyright 2013 Brett Slatkin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility for doing a diff between two corresponding lists of pairs of URLs.

Example usage:

./dpxdt/tools/url_pairs_diff.py \
    --upload_build_id=1234 \
    --release_server_prefix=https://my-dpxdt-apiserver.example.com/api \
    --release_client_id=<your api key> \
    --release_client_secret=<your api secret> \
    before_url_list.txt \
    corresponding_after_list.txt
"""

import HTMLParser
import Queue
import datetime
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import urlparse

# Local Libraries
import gflags
FLAGS = gflags.FLAGS

# Local modules
from dpxdt.client import fetch_worker
from dpxdt.client import release_worker
from dpxdt.client import workers
import flags


class UrlPairsDiff(workers.WorkflowItem):
    """Workflow for diffing a pair of URLs.

    Args:
        new_url: URL of the newest and best version of the page.
        baseline_url: URL of the baseline to compare to.
        upload_build_id: Optional. Build ID of the site being compared. When
            supplied a new release will be cut for this build comparing it
            to the last good release.
        upload_release_name: Optional. Release name to use for the build. When
            not supplied, a new release based on the current time will be
            created.
        heartbeat: Function to call with progress status.
    """

    def run(self,
            new_url_list_file,
            baseline_url_list_file,
            upload_build_id,
            upload_release_name=None,
            heartbeat=None):
        # TODO: Make the default release name prettier.
        if not upload_release_name:
            upload_release_name = str(datetime.datetime.utcnow())

        baseline_urls = [line.strip() for line in open(baseline_url_list_file, 'r').readlines()]
        new_urls = [line.strip() for line in open(new_url_list_file, 'r').readlines()]

        if len(baseline_urls) != len(new_urls):
                print('length of URL lists is not equal')
                sys.exit(1)

        total_urls = len(new_urls)
        if total_urls == 0:
                print('number of URLs cannot be zero')
                sys.exit(1)

        release_url = new_urls[0]

        yield heartbeat('Creating release %s' % upload_release_name)
        release_number = yield release_worker.CreateReleaseWorkflow(
            upload_build_id, upload_release_name, release_url)

        config_dict = {
            'viewportSize': {
                'width': 1280,
                'height': 1024,
            }
        }
        if FLAGS.inject_css:
            config_dict['injectCss'] = FLAGS.inject_css
        if FLAGS.inject_js:
            config_dict['injectJs'] = FLAGS.inject_js
        config_data = json.dumps(config_dict)

        for i in range(total_urls):
                baseline_url = baseline_urls[i]
                new_url = new_urls[i]

                url_parts = urlparse.urlparse(new_url)

                #yield heartbeat('Requesting capture for pair %d/%d' % (i+1, total_urls))
                yield heartbeat('Requesting capture for pair %d/%d (%s and %s)' % (i+1, total_urls, baseline_url, new_url))
                yield release_worker.RequestRunWorkflow(
                        upload_build_id,
                        upload_release_name,
                        release_number,
                        url_parts.path or '/',
                        new_url,
                        config_data,
                        ref_url=baseline_url,
                        ref_config_data=config_data)

        yield heartbeat('Marking runs as complete')
        release_url = yield release_worker.RunsDoneWorkflow(
            upload_build_id, upload_release_name, release_number)

        yield heartbeat('Results viewable at: %s' % release_url)


def real_main(new_url_list_file=None,
              baseline_url_list_file=None,
              upload_build_id=None,
              upload_release_name=None):
    """Runs the url_pairs_diff."""
    coordinator = workers.get_coordinator()
    fetch_worker.register(coordinator)
    coordinator.start()

    item = UrlPairsDiff(
        new_url_list_file,
        baseline_url_list_file,
        upload_build_id,
        upload_release_name=upload_release_name,
        heartbeat=workers.PrintWorkflow)
    item.root = True

    coordinator.input_queue.put(item)
    coordinator.wait_one()
    coordinator.stop()
    coordinator.join()


def main(argv):
    try:
        argv = FLAGS(argv)
    except gflags.FlagsError, e:
        print '%s\nUsage: %s ARGS\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    if len(argv) != 3:
        print 'Must supply two URLs as arguments.'
        sys.exit(1)

    assert FLAGS.upload_build_id
    assert FLAGS.release_server_prefix

    if FLAGS.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    real_main(
        new_url_list_file=argv[2],
        baseline_url_list_file=argv[1],
        upload_build_id=FLAGS.upload_build_id,
        upload_release_name=FLAGS.upload_release_name)


if __name__ == '__main__':
    main(sys.argv)
