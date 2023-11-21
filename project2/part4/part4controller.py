# Part 4 of UWCSE's Mininet-SDN project
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, IPAddr6, EthAddr

log = core.getLogger()

# Convenience mappings of hostnames to ips
IPS = {
    "h10": "10.0.1.10",
    "h20": "10.0.2.20",
    "h30": "10.0.3.30",
    "serv1": "10.0.4.10",
    "hnotrust": "172.16.10.100",
}

# Convenience mappings of hostnames to subnets
SUBNETS = {
    "h10": "10.0.1.0/24",
    "h20": "10.0.2.0/24",
    "h30": "10.0.3.0/24",
    "serv1": "10.0.4.0/24",
    "hnotrust": "172.16.10.0/24",
}


class Part4Controller(object):
    """
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        print(connection.dpid)
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection
        # Keep track of the hosts that are on each port.
        self.ip_to_port = {}

        # This binds our PacketIn event listener
        connection.addListeners(self)
        # use the dpid to figure out what switch is being created
        if connection.dpid == 1:
            self.s1_setup()
        elif connection.dpid == 2:
            self.s2_setup()
        elif connection.dpid == 3:
            self.s3_setup()
        elif connection.dpid == 21:
            self.cores21_setup()
        elif connection.dpid == 31:
            self.dcs31_setup()
        else:
            print("UNKNOWN SWITCH")
            exit(1)

    def s1_setup(self):
        # put switch 1 rules here
        # Flood all traffic coming into s1
        match = of.ofp_match()
        action = of.ofp_action_output(port=of.OFPP_FLOOD)
        self.connection.send(of.ofp_flow_mod(match=match, actions=[action]))

    def s2_setup(self):
        # put switch 2 rules here
        # Flood all traffic coming into s2
        match = of.ofp_match()
        action = of.ofp_action_output(port=of.OFPP_FLOOD)
        self.connection.send(of.ofp_flow_mod(match=match, actions=[action]))

    def s3_setup(self):
        # put switch 3 rules here
        # Flood all traffic coming into s3
        match = of.ofp_match()
        action = of.ofp_action_output(port=of.OFPP_FLOOD)
        self.connection.send(of.ofp_flow_mod(match=match, actions=[action]))

    def cores21_setup(self):
        # put core switch rules here
        # Block untrusted host's ICMP and IP traffic to serv1
        match = of.ofp_match()
        match.dl_type = 0x800  # IP type
        match.nw_src = IPAddr(IPS["hnotrust"])
        match.nw_dst = IPAddr(IPS["serv1"])
        self.connection.send(of.ofp_flow_mod(match=match, command=of.OFPFC_ADD))

        # Block any ICMP traffic from the untrusted host.
        match = of.ofp_match()
        match.dl_type = 0x800  # IP type
        match.nw_src = IPAddr(IPS["hnotrust"])
        match.nw_proto = 1  # ICMP protocol
        self.connection.send(of.ofp_flow_mod(match=match, command=of.OFPFC_ADD))

    def dcs31_setup(self):
        # put datacenter switch rules here
        # Flood all traffic coming into dcs31
        match = of.ofp_match()
        action = of.ofp_action_output(port=of.OFPP_FLOOD)
        self.connection.send(of.ofp_flow_mod(match=match, actions=[action]))

    # used in part 4 to handle individual ARP packets
    # not needed for part 3 (USE RULES!)
    # causes the switch to output packet_in on out_port
    def resend_packet(self, packet_in, out_port):
        msg = of.ofp_packet_out()
        msg.data = packet_in
        action = of.ofp_action_output(port=out_port)
        msg.actions.append(action)
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        """
        Packets not handled by the router rules will be
        forwarded to this method to be handled by the controller
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.
        # Handle ARP requests across subnets
        if packet.type == packet.ARP_TYPE:
            self.handle_arp(packet, packet_in)
        # Forward IP packets, reply if they're ICMP pings to the router
        elif packet.type == packet.IP_TYPE:
            self.handle_ipv4(packet, packet_in)
        # Flood all other packets
        else:
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.buffer_id = packet_in.buffer_id
            msg.in_port = packet_in.in_port
            self.connection.send(msg)

    def handle_arp(self, packet, packet_in):
        arp = packet.payload
        if arp.opcode == arp.REQUEST:
            arp_addr = IPAddr(arp.protosrc)
            if arp_addr in self.ip_to_port:
                # Create ARP reply packet
                arp_reply = arp
                arp_reply.hwsrc = arp.hwsrc
                arp_reply.hwdst = arp.hwdst
                arp_reply.opcode = arp.REPLY
                arp_reply.protosrc = arp.protodst
                arp_reply.protodst = arp.protosrc
                self.resend_packet(arp_reply.pack(), packet_in.in_port)

            # Learn the port from the request
            self.ip_to_port[arp_addr] = packet_in.in_port
        elif arp.opcode == arp.REPLY:
            # Learn the port from the reply
            arp_addr = IPAddr(arp.protosrc)
            self.ip_to_port[arp_addr] = packet_in.in_port

    def handle_ipv4(self, packet, packet_in):
        ipv4 = packet.payload
        ipv4_addr = IPAddr(ipv4.dstip)
        if ipv4_addr in self.ip_to_port:
            self.resend_packet(packet, self.ip_to_port[ipv4_addr])
        else:
            self.resend_packet(packet, of.OFPP_FLOOD)


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Part4Controller(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
