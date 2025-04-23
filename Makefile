PREFIX = /usr

.PHONY: all clean

all:
	-@echo do nothing

clean:
	-@echo do nothing

install:
	install -Dm0755 serial_tool.py $(DESTDIR)$(PREFIX)/bin/serial_tool
