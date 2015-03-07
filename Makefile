.PHONY: all clean

all:
clean :

install: all
	install -m 0755 serial_tool.py  $(DESTDIR)/usr/bin/serial_tool




