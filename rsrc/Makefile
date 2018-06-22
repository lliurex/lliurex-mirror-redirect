NO_COLOR    = \x1b[0m
BUILD_COLOR    = \x1b[32;01m
CLEAN_COLOR    = \x1b[31;01m


FILES:=$(patsubst %.svg,%.png,$(wildcard *.svg))

	
all: $(FILES)

%.png : %.svg
	@echo -e '$(BUILD_COLOR)* Rendering [$@]$(NO_COLOR)' 
	inkscape $< -z -e=$@ 2>/dev/null

	@echo -e '$(BUILD_COLOR)* Copying $@ to ../$(patsubst %.png,%.install,$@)/usr/share/banners/lliurex-neu/$(NO_COLOR)' 
	cp $@ ../$(patsubst %.png,%.install,$@)/usr/share/banners/lliurex-neu/
	
clean:
	@echo -e '$(CLEAN_COLOR)* Cleaning...$(NO_COLOR)' 
	rm -rf $(patsubst %.svg,%.png,$(wildcard *.svg))
	
	
