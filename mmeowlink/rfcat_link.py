
# Based on decoding-carelink/decocare/link.py

import logging
import decocare.lib as lib
import decocare.fuser as fuser
import time
io  = logging.getLogger( )
log = io.getChild(__name__)
from fourbysix import FourBySix

from rflib import *

class NotImplementedException (Exception):
  pass


def setup_medtronic_mmcommander(self, locale='US'):
    self.getRadioConfig()
    rc = self.radiocfg
    rc.sync1          = 0xff
    rc.sync0          = 0x00
    rc.pktlen         = 0xff
    rc.pktctrl1       = 0x00
    rc.pktctrl0       = 0x00
    rc.addr           = 0x00
    rc.fsctrl1        = 0x06
    rc.fsctrl0        = 0x00

    # EU:
    rc.freq2          = 0x24
    rc.freq1          = 0x2e
    rc.freq0          = 0x38
    rc.channr         = 0x00
    rc.pa_table1      = 0x50 # 52 in USA?

    # US
    if locale == 'US':
      rc.freq2        = 0x26
      rc.freq1        = 0x30
      rc.freq0        = 0x00
      rc.channr       = 0x02
      rc.pa_table1    = 0x50 # 52 in USA?

    rc.mdmcfg4        = 0xb9
    rc.mdmcfg3        = 0x66
    rc.mdmcfg2        = 0x33
    rc.mdmcfg1        = 0x61
    rc.mdmcfg0        = 0xe6
    rc.deviatn        = 0x15
    rc.mcsm2          = 0x07
    rc.mcsm1          = 0x30
    rc.mcsm0          = 0x18
    rc.foccfg         = 0x17
    rc.bscfg          = 0x6c
    rc.agcctrl2       = 0x03
    rc.agcctrl1       = 0x40
    rc.agcctrl0       = 0x91
    rc.frend1         = 0x56
    rc.frend0         = 0x11
    rc.fscal3         = 0xe9
    rc.fscal2         = 0x2a
    rc.fscal1         = 0x00
    rc.fscal0         = 0x1f
    rc.test2          = 0x88
    rc.test1          = 0x31
    rc.test0          = 0x09
    rc.pa_table7      = 0x00
    rc.pa_table6      = 0x00
    rc.pa_table5      = 0x00
    rc.pa_table4      = 0x00
    rc.pa_table3      = 0x00
    rc.pa_table2      = 0x00
    rc.pa_table0      = 0x00
    self.setRadioConfig()

class Link( object ):
  __timeout__ = 2
  port = None
  rfcat = None

  def __init__( self, port=None, timeout=None, locale='US' ):
    self.locale = locale

    if timeout is not None:
      self.__timeout__ = timeout

    self.open()

  def open( self, newPort=None, **kwds ):
    if 'timeout' not in kwds:
      kwds['timeout'] = self.__timeout__

    if not self.rfcat:
      print("Loading rfcat")
      self.rfcat = RfCat()
      setup_medtronic_mmcommander(self.rfcat, self.locale)
      self.rfcat.setMaxPower()
      self.reset_rfcat()

    log.info( '{agent} started RfCat library'
      .format(agent=self.__class__.__name__ ))

  def close( self ):
    io.info( 'deallocating rfcat' )
    self.rfcat = None
    return True

  def write( self, string ):
    self.rfcat.RFxmit(string)
    self.reset_rfcat()
    io.info( 'usb.write.len: %s\n%s' % ( len( string ),
                                         lib.hexdump( bytearray( string ) ) ) )
    return len(string)

  def repeat_write( self, string, repeat ):
    for _ in range(0, repeat):
      self.rfcat.RFxmit(string)
      self.reset_rfcat()

    io.info( 'usb.write.len(%s repetitions): %s\n%s' % ( repeat, len( string ),
                                         lib.hexdump( bytearray( string ) ) ) )
    return len(string)

    r = self.rfcat.RFrecv(timeout=5000)

  def read( self ):
    rfcat_response = self.rfcat.RFrecv(timeout=5000)
    self.reset_rfcat()

    r = rfcat_response[0].split('\x00')[0]
    io.info('read encoded %r' % r)
    io.info('read decoded %s' % FourBySix.decode(bytearray(r)))
    # io.info( 'usb.read.raw:\n%s' % ( lib.hexdump( bytearray( r[0] ) ) ) )
    return r

  def readline( self ):
    raise NotImplementedException("readline currently not implemented")

  def readlines( self ):
    raise NotImplementedException("readlines currently not implemented")

  # Workaround for https://bitbucket.org/atlas0fd00m/rfcat/issues/8/first-packet-receive-ok-but-cannot-receive - FIXME
  def reset_rfcat( self ):
    self.rfcat.makePktFLEN(255)
