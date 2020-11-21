.DEFAULT_GOAL := help

##
## Available Goals:
##

##   devdeps : Install all development dependencies
##
.PHONY : devdeps
devdeps :
	@pip install -r requirements-dev.txt


##   help    : Print this help message
##
.PHONY : help
help : Makefile
	@sed -n 's/^##//p' $<
