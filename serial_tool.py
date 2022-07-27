#!/usr/bin/python3

import argparse
import binascii
import logging
import os.path
import re
import readline
import sys
import time

import serial
import termcolor


class SimpleCompleter(object):
    def __init__(self):
        self.options = set(["exit"])
        return

    def add_option(self, option):
        self.options.add(option)

    def complete(self, text, state):
        # ~ print text, state
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s for s in self.options if s and s.startswith(text)]
                # ~ logging.debug('%s matches: %s', repr(text), self.matches)
            else:
                self.matches = sorted(self.options)
                # ~ logging.debug('(empty input) matches: %s', self.matches)

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
        except IndexError:
            response = None

        return response


def unhexlify(s):
    s = re.sub(r"[^0-9a-fA-F]", "", s)
    return binascii.unhexlify(s)


def hexlify(s):
    return " ".join(binascii.hexlify(c).upper() for c in s)


def main():
    parser = argparse.ArgumentParser(
        description="serial_tool - interactive hex serial port console",
        add_help=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-b", "--baud", dest="baud", type=int, help="Baud rate", default=9600)

    parser.add_argument(
        "-p",
        "--parity",
        dest="parity",
        type=str,
        help="set parity, one of [%s]" % ", ".join(serial.Serial.PARITIES),
        default="N",
    )

    parser.add_argument(
        "-d",
        "--data-bits",
        dest="data_bits",
        type=int,
        help="set number of data bits, i.e. bytesize",
        default=8,
    )

    parser.add_argument(
        "-s",
        "--stop-bits",
        dest="stop_bits",
        type=float,
        help="set number of stop bits, one of [%s]" % ", ".join(str(x) for x in serial.Serial.STOPBITS),
        default=1,
    )

    parser.add_argument(
        "-t",
        "--timeout",
        dest="read_timeout",
        type=float,
        help="number of seconds to wait for answer",
        default=1,
    )

    parser.add_argument(
        "--batch",
        dest="batch_mode",
        type=str,
        help="Batch mode, argument is hex string to send. Answer is returned to stdout",
        default=None,
    )

    parser.add_argument("port", type=str, help="Serial port to open, i.e. /dev/ttyXXX")
    args = parser.parse_args()

    if args.baud not in serial.Serial.BAUDRATES:
        print(termcolor.colored("ERROR:", "red"), "incorrect baudrate %d" % args.baud)
        return 1

    if args.parity not in serial.Serial.PARITIES:
        print(termcolor.colored("ERROR:", "red"), "incorrect parity %s" % args.parity)
        return 1

    if args.stop_bits not in serial.Serial.STOPBITS:
        print(termcolor.colored("ERROR:", "red"), "incorrect stop bits setting %d" % args.stop_bits)
        return 1

    # configure the serial connections (the parameters differs on the device you are connecting to)
    ser = serial.Serial(
        port=args.port,
        baudrate=args.baud,
        parity=args.parity,
        stopbits=args.stop_bits,
        bytesize=args.data_bits,
    )

    if args.batch_mode:
        do_batch_mode(args, ser)
    else:
        do_interactive_mode(args, ser)


def do_batch_mode(args, ser):
    try:
        input_hex = unhexlify(args.batch_mode)
    except TypeError as e:
        print(termcolor.colored("ERROR: " + e.message, "red"), file=sys.stderr)
    else:
        ser.write(input_hex)
        out = ""

        # wait before reading output
        time.sleep(args.read_timeout)
        while ser.inWaiting() > 0:
            out += ser.read(1)

        if out != "":

            print(hexlify(out))


def do_interactive_mode(args, ser):
    print(
        "serial_tool on %s: %d %s%s%s" % (ser.portstr, ser.baudrate, ser.bytesize, ser.parity, ser.stopbits)
    )
    print(
        "Enter your commands below in HEX form. \r\nAll characters but 0-9,a-f including spaces are ignored.\r\nPress Control-D or Control-C to leave the application.\r\nPress [Enter] to print received data"
    )

    input = 1
    while 1:
        # get keyboard input
        try:
            input = raw_input(termcolor.colored(">> ", "red", attrs=["bold"]))
        except (KeyboardInterrupt, EOFError):
            print("exiting")
            ser.close()
            return

        if input == "exit":
            ser.close()
            return
        else:
            # send the character to the device
            # (note that I happend a \r\n carriage return and line feed to the characters - this is requested by my device)

            try:
                input_hex = unhexlify(input)
            except TypeError as e:
                print(termcolor.colored("ERROR: " + e.message, "red"))
            else:

                ser.write(input_hex)
                out = ""

                # wait before reading output
                time.sleep(args.read_timeout)
                while ser.inWaiting() > 0:
                    out += ser.read(1)

                if out != "":
                    print(termcolor.colored("<< ", "green", attrs=["bold"]) + hexlify(out))


if __name__ == "__main__":
    readline_hist_file = os.path.expanduser("~/.serial_tool.history")
    try:
        readline.read_history_file(readline_hist_file)
    except IOError:
        pass

    readline.set_history_length(2000)
    readline.parse_and_bind("set editing-mode vi")

    try:
        rc = main()
    finally:
        readline.write_history_file(readline_hist_file)
    sys.exit(rc)
