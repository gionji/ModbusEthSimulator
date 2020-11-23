#!/usr/bin/env python
"""
Pymodbus Synchronous Client Examples
--------------------------------------------------------------------------

The following is an example of how to use the synchronous modbus client
implementation from pymodbus.

It should be noted that the client can also be used with
the guard construct that is available in python 2.5 and up::

    with ModbusClient('127.0.0.1') as client:
        result = client.read_coils(1,10)
        print result
"""


import FdsCommon as fds
import time

from pymodbus.exceptions import ModbusIOException
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
# from pymodbus.client.sync import ModbusUdpClient as ModbusClient
# from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# --------------------------------------------------------------------------- #
# configure the client logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

UNIT = 0x1


def run_sync_client():

    client = ModbusClient('localhost', port=5020)

    client.connect()

    # ------------------------------------------------------------------------#
    # specify slave to query
    # ------------------------------------------------------------------------#
    # The slave to query is specified in an optional parameter for each
    # individual request. This can be done by specifying the `unit` parameter
    # which defaults to `0x00`
    # ----------------------------------------------------------------------- #
    log.debug("Reading Coils")
    rr = client.read_coils(1, 1, unit=UNIT)
    log.debug(rr)


    data = getChargeControllerData(client, modbusUnit=0x01)
    print( data )
    # ----------------------------------------------------------------------- #
    # close the client
    # ----------------------------------------------------------------------- #
    client.close()


def getChargeControllerData( client, modbusUnit):
    data = {'type':'chargecontroller'}

    if client != None:
        try:
            # read registers. Start at 0 for convenience
            rr = client.read_holding_registers(0, 80, unit=modbusUnit)

            # for all indexes, subtract 1 from what's in the manual
            V_PU_hi = rr.registers[0]
            V_PU_lo = rr.registers[1]
            I_PU_hi = rr.registers[2]
            I_PU_lo = rr.registers[3]

            V_PU = float(V_PU_hi) + float(V_PU_lo)
            I_PU = float(I_PU_hi) + float(I_PU_lo)

            v_scale = V_PU * 2**(-15)
            i_scale = I_PU * 2**(-15)
            p_scale = V_PU * I_PU * 2**(-17)

            # battery sense voltage, filtered
            data[ fds.LABEL_CC_BATTS_V ]       = rr.registers[24] * v_scale
            data[ fds.LABEL_CC_BATT_SENSED_V ] = rr.registers[26] * v_scale
            data[ fds.LABEL_CC_BATTS_I ]       = rr.registers[28] * i_scale
            data[ fds.LABEL_CC_ARRAY_V ]       = rr.registers[27] * v_scale
            data[ fds.LABEL_CC_ARRAY_I ]       = rr.registers[29] * i_scale
            data[ fds.LABEL_CC_STATENUM ]     = rr.registers[50]
            data[ fds.LABEL_CC_HS_TEMP]       = rr.registers[35]
            data[ fds.LABEL_CC_RTS_TEMP]      = rr.registers[36]
            data[ fds.LABEL_CC_OUT_POWER]     = rr.registers[58] * p_scale
            data[ fds.LABEL_CC_IN_POWER]      = rr.registers[59] * p_scale
            data[ fds.LABEL_CC_MINVB_DAILY ]  = rr.registers[64] * v_scale
            data[ fds.LABEL_CC_MAXVB_DAILY ]  = rr.registers[65] * v_scale
            data[ fds.LABEL_CC_MINTB_DAILY ]  = rr.registers[71]
            data[ fds.LABEL_CC_MAXTB_DAILY ]  = rr.registers[72]
            data[ fds.LABEL_CC_DIPSWITCHES ]  = bin(rr.registers[48])[::-1][:-2].zfill(8)
            #led_state            = rr.registers
        except ModbusIOException as e:
            logging.error('Charge Controller: modbusIOException')
            raise e
        except Exception as e:
            logging.error('Charge Controller: unpredicted exception')
            raise e

    return data


if __name__ == "__main__":
    while True:
        try:
            run_sync_client()
        except Exception as e:
            print( str(e) )

        time.sleep(2.0)
