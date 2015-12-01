FIND = find
PDFTK = pdftk
PYLINT = pylint
PYTHON = python
# PYTHON = env LC_MESSAGES=de_DE.UTF-8 python
# PYTHON = env LANG=de_DE.UTF-8 python
# PYTHON = env LC_ALL=de_DE.UTF-8 python
RM = rm

CLEAN_FILES =

LANGUAGES =
LANGUAGES += en
LANGUAGES += de

MODES =
MODES += mark
MODES += history

DAT_FILES := $(sort $(wildcard *.dat))

PDF_DRIVERS =
PDF_DRIVERS += cairo
PDF_DRIVERS += tikz

ALL_PDF_TARGETS =
ALL_PDF_TARGETS += $(foreach lang,$(LANGUAGES),$(foreach mode,$(MODES),$(foreach driver,$(PDF_DRIVERS),$(patsubst %.dat,%.$(driver).$(mode).$(lang).pdf,$(DAT_FILES)))))

PDF_ALL_TARGETS =
# PDF_ALL_TARGETS += $(patsubst %.dat,%.all.pdf,$(DAT_FILES))
PDF_ALL_TARGETS += $(foreach lang,$(LANGUAGES),$(foreach mode,$(MODES),$(patsubst %.dat,%.ALL.$(mode).$(lang).pdf,$(DAT_FILES))))

ALL_TARGETS =
# ALL_TARGETS += $(patsubst %.dat,%.cairo.eps,$(DAT_FILES))
# ALL_TARGETS += $(patsubst %.dat,%.cairo.png,$(DAT_FILES))
# ALL_TARGETS += $(patsubst %.dat,%.cairo.svg,$(DAT_FILES))
ALL_TARGETS += $(ALL_PDF_TARGETS)
ALL_TARGETS += $(PDF_ALL_TARGETS)

-include locals.mk

.PHONY: all
all: update-locale

.PHONY: plots
plots: all $(ALL_TARGETS)

PY_MAIN = wcg-cli

PY_FILES =
PY_FILES += weightgrid/__init__.py
PY_FILES += weightgrid/cli.py
PY_FILES += weightgrid/gui.py
PY_FILES += weightgrid/log.py
PY_FILES += weightgrid/drivers/__init__.py
PY_FILES += weightgrid/drivers/basic.py

PY_FILES_CAIRO = weightgrid/drivers/Cairo.py
PY_FILES_TIKZ  = weightgrid/drivers/TikZ.py

ALL_PY_FILES =
ALL_PY_FILES += $(PY_FILES)
ALL_PY_FILES += $(PY_FILES_CAIRO)
ALL_PY_FILES += weightgrid/drivers/ReportLab.py
ALL_PY_FILES += $(PY_FILES_TIKZ)

.PHONY: pylint
pylint:
	$(PYLINT) --rcfile pylint.rc $(PY_MAIN) $(PY_FILES)

PYDOC = $(PYTHON) -m pydoc

.PHONY: pydoc
pydoc:
	$(PYDOC) -w "$(PWD)"
	rm -rf pydoc
	mkdir pydoc
	mv weightgrid*.html pydoc/

.PHONY: sloccount
sloccount:
	$(SLOCCOUNT) --details wcg-cli wcg-gui weightgrid

PACKAGE_NAME = weight-calendar-grid
GUI_PROGRAM_NAME = wcg-gui
PROGRAM_NAME = $(PY_MAIN)
PACKAGE_VERSION = 0.1.1-borked

.PHONY: check
check: all test-wcg $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) test-wcg


TEXT_DOMAIN = $(PACKAGE_NAME)
COPYRIGHT_HOLDER = 'Hans Ulrich Niedermann <hun@n-dimensional.de>'
BUG_ADDRESS = 'Hans Ulrich Niedermann <hun@n-dimensional.de>'

.PHONY: update-po
update-po:
	set -ex; \
	cd po; \
	xgettext -L Python \
		$(foreach f,$(PY_MAIN) $(ALL_PY_FILES),../$(f)) \
		--foreign-user \
		--copyright-holder="$(COPYRIGHT_HOLDER)" \
		--package-name="$(PACKAGE_NAME)" \
		--package-version="$(PACKAGE_VERSION)" \
		--msgid-bugs-address="$(BUG_ADDRESS)" \
		-d "$(TEXT_DOMAIN)" -o "$(TEXT_DOMAIN).pot"; \
	for po in *.po; do \
		if msgmerge "$$po" "$(TEXT_DOMAIN).pot" > "$$po.new"; then \
			mv -f "$$po.new" "$$po"; \
		else \
			s="$$?"; \
			rm -f "$$po.new"; \
			exit "$$s"; \
		fi; \
	done

ifndef DUMMY
dummy := $(shell $(MAKE) update-locale DUMMY=foo)
endif

.PHONY: update-locale
update-locale:
	set -ex; \
	for po in po/*.po; do \
		lang="$$(basename "$$po" .po)"; \
		msgdir="locale/$${lang}/LC_MESSAGES"; \
		mkdir -p "$$msgdir"; \
		msgfmt -c -o "$${msgdir}/$(TEXT_DOMAIN).mo" "$$po"; \
	done

.PHONY: clean
clean:
	$(RM) -f $(ALL_TARGETS)
	$(FIND) weightgrid -type f -name '*.py[co]' -print -delete
	$(RM) -rf locale
	$(RM) -rf pydoc
	@set -x && $(RM) -f test--*.pdf
	$(RM) -f $(CLEAN_FILES)

