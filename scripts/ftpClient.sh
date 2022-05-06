#!/bin/sh
ftp -n localhost 2121 << EOF
quote USER user
quote PASS passwd
put sample.txt
quit
EOF
