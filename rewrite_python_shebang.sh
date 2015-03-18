#!/bin/bash

for file in `grep -Rl '^#!/usr/bin/env python$' .`; do
	echo modifying $file
	sed -i -e 's~^#!/usr/bin/env python$~#!/usr/bin/env python2.7~' $file
done
