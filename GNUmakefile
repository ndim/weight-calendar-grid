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

WG_ARGS =

-include locals.mk

# some default demo values
HEIGHT ?= 1.80
KG_RANGE ?= auto

.PHONY: all
all: update-locale

.PHONY: plots
plots: all $(ALL_TARGETS)

PY_MAIN = plot-wcg

PY_FILES =
PY_FILES += weightgrid/__init__.py
PY_FILES += weightgrid/cmdline.py
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
	sloccount --details $(PY_MAIN) weightgrid


.PHONY: pdf
pdf: $(ALL_PDF_TARGETS) $(PDF_ALL_TARGETS)


PACKAGE_NAME = weight-calendar-grid
PROGRAM_NAME = $(PY_MAIN)
PACKAGE_VERSION = 0.1.1

VERSION_PY = weightgrid/version.py
PY_FILES += weightgrid/version.py
CLEAN_FILES += weightgrid/version.py
weightgrid/version.py: GNUmakefile
	echo '# Automatically generated from GNUmakefile' > $(VERSION_PY).new
	echo '"""Automatically generated version data (from GNUmakefile)"""' >> $(VERSION_PY).new
	echo 'package_name = "$(PACKAGE_NAME)"' >> $(VERSION_PY).new
	echo 'package_version = "$(PACKAGE_VERSION)"' >> $(VERSION_PY).new
	echo 'program_name = "$(PROGRAM_NAME)"' >> $(VERSION_PY).new
	echo '# End of file.' >> $(VERSION_PY).new
	set -x; if cmp "$(VERSION_PY).new" "$(VERSION_PY)"; then \
		rm -f "$(VERSION_PY).new"; \
	else \
		mv -f "$(VERSION_PY).new" "$(VERSION_PY)"; \
	fi


.PHONY: check
check: all test-wcg $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) test-wcg


TEXT_DOMAIN = plot-weight-calendar-grid
COPYRIGHT_HOLDER = 'Hans Ulrich Niedermann <hun@n-dimensional.de>'
BUG_ADDRESS = 'Hans Ulrich Niedermann <hun@n-dimensional.de>'

.PHONY: update-po
update-po: weightgrid/version.py
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
update-locale: weightgrid/version.py
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

# WG_ARGS += --dry-run
WG_ARGS += --keep
# WG_ARGS += --quiet
# WG_ARGS += --verbose
# WG_ARGS += --verbose
# WG_ARGS += --verbose
# WG_ARGS += --verbose
# WG_ARGS += --begin=2013-01-13
WG_ARGS += --height $(HEIGHT)
WG_ARGS += --weight $(KG_RANGE)


%.all.pdf: $(foreach lang,$(LANGUAGES),$(foreach driver,$(PDF_DRIVERS),%.$(driver).$(lang).pdf))
	$(PDFTK) $^ cat output $@


%.ALL.pdf: $(foreach driver,$(PDF_DRIVERS),%.$(driver).pdf)
	$(PDFTK) $^ cat output $@

%.cairo.eps: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --input=$< --output=$@ $(WG_FLAGS) $(WG_ARGS)

%.cairo.pdf: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --input=$< --output=$@ $(WG_FLAGS) $(WG_ARGS)

%.cairo.png: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --input=$< --output=$@ $(WG_FLAGS) $(WG_ARGS)

%.cairo.svg: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --input=$< --output=$@ $(WG_FLAGS) $(WG_ARGS)

%.tikz.pdf: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_TIKZ)
	$(PYTHON) $(PY_MAIN) --driver=tikz  --input=$< --output=$@ $(WG_FLAGS) $(WG_ARGS)

define RULESET_template

%.ALL.$(2).$(1).pdf: $$(foreach driver,$$(PDF_DRIVERS),%.$$(driver).$(2).$(1).pdf)
	$(PDFTK) $$^ cat output $$@

%.cairo.$(2).$(1).eps: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --lang=$(1) --mode=$(2) --input=$$< --output=$$@ $(WG_FLAGS) $(WG_ARGS)

%.cairo.$(2).$(1).pdf: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --lang=$(1) --mode=$(2) --input=$$< --output=$$@ $(WG_FLAGS) $(WG_ARGS)

%.cairo.$(2).$(1).png: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --lang=$(1) --mode=$(2) --input=$$< --output=$$@ $(WG_FLAGS) $(WG_ARGS)

%.cairo.$(2).$(1).svg: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_CAIRO)
	$(PYTHON) $(PY_MAIN) --driver=cairo --lang=$(1) --mode=$(2) --input=$$< --output=$$@ $(WG_FLAGS) $(WG_ARGS)

%.tikz.$(2).$(1).pdf: %.dat $(PY_MAIN) $(PY_FILES) $(PY_FILES_TIKZ)
	$(PYTHON) $(PY_MAIN) --driver=tikz  --lang=$(1) --mode=$(2) --input=$$< --output=$$@ $(WG_FLAGS) $(WG_ARGS)

endef

$(foreach mode,$(MODES),$(foreach lang,$(LANGUAGES),$(eval $(call RULESET_template,$(lang),$(mode)))))
