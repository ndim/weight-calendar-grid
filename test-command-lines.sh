#!/bin/sh

# TODO: Migrate these to a minimized number of test cases for maximum
#       code coverage Python3 unittest/nose tests.

set -ex

py_main="plot-wcg"

# Common options
python ${py_main} --version
python ${py_main} --help

# Check kg range parsing
python ${py_main} --dry-run --driver=cairo --output=test.out --height=1.78
python ${py_main} --dry-run --driver=cairo --output=test.out --height=1.78 --weight=auto
python ${py_main} --dry-run --driver=cairo --output=test.out --height=1.78 --weight=76
python ${py_main} --dry-run --driver=cairo --output=test.out --height=1.78 --weight=80-90
python ${py_main} --dry-run --driver=cairo --output=test.out --height=1.78 --weight=82+-4

args="--output=test.out --height=1.78"

# driver/format args
python ${py_main} --dry-run --driver=cairo              ${args}
# python ${py_main} --dry-run --format=png --driver=cairo ${args}
python ${py_main} --dry-run --driver=cairo --format=png ${args}
python ${py_main} --dry-run --driver=cairo --format=pdf ${args}
python ${py_main} --dry-run --driver=tikz               ${args}
python ${py_main} --dry-run --driver=tikz --format=pdf  ${args}
# python ${py_main} --dry-run --driver=tikz --format=foo ${args}

args="--driver=cairo ${args}"

# begin date tests
python ${py_main} --dry-run           -b 2011-12-31 ${args}
python ${py_main} --dry-run      --begin 2011-12-31 ${args}
python ${py_main} --dry-run --begin-date 2011-12-31 ${args}

# end date with given begin date
# python ${py_main} --dry-run -b 2011-12-31 -e 2010-12-31 ${args}
# python ${py_main} --dry-run -b 2011-12-31 -e 2011-12-31 ${args}
python ${py_main} --dry-run -b 2011-12-31 -e 2012-12-31 ${args}

# End of file.
