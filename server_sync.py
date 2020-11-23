#!/usr/bin/env python
"""
Pymodbus Synchronous Server Example
--------------------------------------------------------------------------

The synchronous server is implemented in pure python without any third
party libraries (unless you need to use the serial protocols which require
pyserial). This is helpful in constrained or old environments where using
twisted is just not feasible. What follows is an example of its use:
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import StartTlsServer
from pymodbus.server.sync import StartUdpServer
from pymodbus.server.sync import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

from pymodbus.exceptions import ModbusIOException

import threading, time, random

#---------------------------------------------------------------------------#
# import the twisted libraries we need
#---------------------------------------------------------------------------#
from twisted.internet.task import LoopingCall

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)


class updaterThread (threading.Thread):

    def __init__(self, context, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self.context  = context

    def run(self):
        while True:
            try:
                self.callback(self, self.context)
                print("/// updating the context")
            except Exception as e:
                print(e)
            finally:
                time.sleep(0.5)




def updating_writer(self, a):
    print("/// updating the context")
    context  = a # retrieve form args the context obj

    register = 0x03    #  to read holding regsters
    slave_id = 0x01 # it's the unit id
    address  = 0 # pstarting address
    count_off = 80

    values   = context[slave_id].getValues(register, address, count=count_off)
    values   = [random.randint(30, 50)  for v in values]

    print( values )

    log.debug("new values: " + str(values))
    context[slave_id].setValues(register, address, values)


'''
V_PU hi, V_PU lo
[1,2][0x0000, 0x0001] (V). voltage scaling.
The scaling value for all voltages. The scaling value is defined as:
Vscaling = whole.fraction = [V_PU hi].[V_PU lo]

Example:
V_PU hi = 0x004E = 78
V_PU lo = 0x03A6 = 934
V_PU lo must be shifted by 16 (divided by 2^16) and then added to V_PU hi
Vscaling = 78 + 934/(2^16) = 78.01425

I_PU hi, I_PU lo
[3,4][0x0002, 0x0003] (V). current scaling.
The scaling value for all currents. The scaling value is defined as:
Iscaling = whole.fraction = [I_PU hi].[I_PU lo]
See the V_PU scaling example above
'''

def cc_updater(self, a):
    print("/// updating the context")
    context  = a # retrieve form args the context obj

    register = 0x03    #  to read holding regsters
    slave_id = 0x01 # it's the unit id
    address  = 0 # pstarting address
    count_off = 80

    V_PU_hi = 0x004E
    V_PU_lo = 0x03A6
    I_PU_hi = 0x004E # TODO: get real values for current
    I_PU_lo = 0x03A6

    V_PU = float(V_PU_hi) + float(V_PU_lo)
    I_PU = float(I_PU_hi) + float(I_PU_lo)

    v_scale = V_PU * 2**(-15)
    i_scale = I_PU * 2**(-15)
    p_scale = V_PU * I_PU * 2**(-17)

    values   = context[slave_id].getValues(register, address, count=count_off)

    val = random.randint(30, 50)

    values[ 24 ] = int( val / v_scale)  # LABEL_CC_BATTS_V
    values[ 28 ] = int(val / i_scale)  # LABEL_CC_BATT_SENSED_V
    values[ 26 ] = int(val / v_scale)  # LABEL_CC_BATTS_I
    values[ 27 ] = int(val / v_scale)  # LABEL_CC_ARRAY_V
    values[ 29 ] = int(val / i_scale)  # LABEL_CC_ARRAY_I
    values[ 50 ] = int(random.randint(0, 9))  # LABEL_CC_STATENUM
    values[ 35 ] = int(val)  # LABEL_CC_HS_TEMP
    values[ 36 ] = int(val)  # LABEL_CC_RTS_TEMP
    values[ 58 ] = int(val / p_scale)  # LABEL_CC_OUT_POWER
    values[ 59 ] = int(val / p_scale)  # LABEL_CC_IN_POWER
    values[ 64 ] = int(val / v_scale)  # LABEL_CC_MINVB_DAILY
    values[ 65 ] = int(val / v_scale)  # LABEL_CC_MAXVB_DAILY
    values[ 71 ] = int(val)  # LABEL_CC_MINTB_DAILY
    values[ 72 ] = int(val)  # LABEL_CC_MAXTB_DAILY
    values[ 72 ] = random.randint(0, 64)  # LABEL_CC_DIPSWITCHES

    # settare i rance veri

    print( values )

    log.debug("new values: " + str(values))
    context[slave_id].setValues(register, address, values)



def run_server():

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0,  [30] * 100), # discrete input space
        co=ModbusSequentialDataBlock(0,  [40] * 100), # c  o  space
        hr = ModbusSequentialDataBlock(0, [17] * 81) , # holding registers space [start addr, value, addr_offset]
        ir=ModbusSequentialDataBlock(0,  [50] * 100),
        ) # input registers space

    context = ModbusServerContext(slaves=store, single=True)

    identity = ModbusDeviceIdentification()
    identity.VendorName  = 'Gionji'
    identity.ProductCode = 'AGB'
    identity.VendorUrl   = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'Pymodbus Server Sim'
    identity.ModelName   = 'Pymodbus  Sim '
    identity.MajorMinorRevision = '0.1'

    # UPDATER
    time = 1
    updater = updaterThread(context, cc_updater)
    updater.start()

    #updating_writer(context)

    StartTcpServer(context, identity=identity, address=("", 5020))



if __name__ == "__main__":
    run_server()
