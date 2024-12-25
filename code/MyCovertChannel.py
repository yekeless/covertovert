from CovertChannelBase import CovertChannelBase
from scapy.all import IP, TCP, sniff
from random import randint
import time



BIT_PER_PACKET = 2 # The number of bits we send in each packet
CHESSBOARD_SIZE = 8
MIN_PACKET_SIZE = 20 # Minimum TCP packet which only includes TCP headers size is 20 

# The first CHESSBOARD_SIZE bits of the packet size is the chessboard, the following BIT_PER_PACKET bits are the negation bits
# length of bit representation of packet size = CHESSBOARD_SIZE + BIT_PER_PACKET

def number_of_ones_in_bit_representation(value: int):
    """
    Calculates the number of ones in the binary representation of the given value
    """
    number_of_ones = 0
    digit = 1
    while digit <= value:
        if value & digit:
            number_of_ones += 1
        digit <<= 1
    return number_of_ones

def xor_result_of_chessboard(chessboard: int):
    """
    Calculates the total XOR result of the coins of the given chessboard
    """
    xor_result = 0
    for i in range(CHESSBOARD_SIZE):
        if chessboard & 1:
            xor_result ^= i
        chessboard >>= 1
    return xor_result

def coin_number_to_flip(chessboard: int, devils_number: int):
    """
    Determines the coin to flip according to the given chessboard and devils number
    """
    xor_result = xor_result_of_chessboard(chessboard)
    coin = xor_result ^ devils_number
    return coin

def turn_parameter_list_into_devils_numbers(lst: list):
    """
    Calculates the devils numbers according to the user input
    """
    result = []
    for element in lst:
        result.append(element % 8)
    return result

def calculate_payload_size(message_bits, devils_numbers):
    """
    Calculates the required payload size according to the given message bits and devils numbers
    """
    if len(message_bits) != BIT_PER_PACKET or len(devils_numbers) != BIT_PER_PACKET:
        raise ValueError("The length of the message bits and parameters should be equal to BIT_PER_PACKET")
    
    minimum_chessboard_size = MIN_PACKET_SIZE // (2 ** BIT_PER_PACKET) + 1 # Minimum packet size is 54
    chessboard = randint(minimum_chessboard_size, 2 ** CHESSBOARD_SIZE - 1)

    negation_bits = 0
    for index in range(BIT_PER_PACKET):
        devils_number = devils_numbers[index]
        message_bit = message_bits[index]

        coin_to_flip = coin_number_to_flip(chessboard, devils_number)

        negation_bits <<= 1
        if number_of_ones_in_bit_representation(coin_to_flip) % 2 != int(message_bit):
            negation_bits += 1

    packet_size = chessboard * (2 ** BIT_PER_PACKET) + negation_bits
    payload_size = packet_size - MIN_PACKET_SIZE # 54 bytes for TCP, IP and LINK headers
    return payload_size

def get_chessboard_from_packet_size(packet_size: int):
    """
    Retrieves the chessboard information from the packet size
    """
    return packet_size // (2 ** BIT_PER_PACKET)

def get_negation_bits_from_packet_size(packet_size: int):
    """
    Retrieves the negation bits from the packet size
    """
    return packet_size % (2 ** BIT_PER_PACKET)



class MyCovertChannel(CovertChannelBase):
    """
    - You are not allowed to change the file name and class name.
    - You can edit the class in any way you want (e.g. adding helper functions); however, there must be a "send" and a "receive" function, the covert channel will be triggered by calling these functions.
    """
    def __init__(self):
        """
        We initialize the received message, bit array and stop flag.
        """
        self.received_message = ""
        self.bit_array = []
        self.stop_flag = False

    def send(self, devils_number_one, devils_number_two, min_sleep_time, max_sleep_time, log_file_name):
        """
        First we measure the start time, then we generate a random binary message with 16 bits. We send the message bit by bit by creating packets with the help of the calculate_payload_size function. We sleep for a random time between min_sleep_time and max_sleep_time after sending each packet. Finally, we measure the end time and print the elapsed time.
        """
        start_time = time.time()
        print(start_time)

        devils_numbers = turn_parameter_list_into_devils_numbers([devils_number_one, devils_number_two])
        binary_message = self.generate_random_binary_message_with_logging(log_file_name, 16, 16)
        msg_len = len(binary_message)
        i = 0
        while i < msg_len:
            message_bits = binary_message[i: i + BIT_PER_PACKET]
            i += BIT_PER_PACKET
            pkt = IP(dst = "172.18.0.3") / TCP(dport = 8000) 
            payload_size = calculate_payload_size(message_bits, devils_numbers)
            payload = "X" * payload_size
            pkt = pkt / payload
            CovertChannelBase().send(pkt)
            CovertChannelBase().sleep_random_time_ms(min_sleep_time,max_sleep_time)
        end_time = time.time()
        print(end_time)
        print("Time elapsed: ", end_time - start_time)

        
    def receive(self, devils_number_one, devils_number_two, log_file_name):
        """
        We create a handle_packet function to handle the incoming packets. We calculate the chessboard and negation bits from the packet size. We determine the coin to flip according to the chessboard and devils number. We calculate the number of ones in the bit representation of the coin to flip
        """

        devils_numbers = turn_parameter_list_into_devils_numbers([devils_number_one, devils_number_two])
        def handle_packet(packet):
            tcp_packet = packet[TCP]
            packet_size = len(tcp_packet)
            chessboard = get_chessboard_from_packet_size(packet_size)
            negation_bits = get_negation_bits_from_packet_size(packet_size)
            for devils_number in devils_numbers:
                coin_to_flip = coin_number_to_flip(chessboard, devils_number)
                number_of_ones = number_of_ones_in_bit_representation(coin_to_flip)
                negation_bit = negation_bits // 2
                negation_bits = negation_bits % 2
                negation_bits <<= 1
                if negation_bit == 0:
                    self.bit_array.append(str(number_of_ones % 2))
                else:
                    if number_of_ones % 2 == 0:
                        self.bit_array.append("1")
                    else:
                        self.bit_array.append("0")

            if len(self.bit_array) == 8:
                received_char = CovertChannelBase().convert_eight_bits_to_character("".join(self.bit_array))
                self.received_message += received_char
                if received_char == ".":
                    self.stop_flag = True
                    self.log_message(self.received_message, log_file_name)
                    return
                self.bit_array.clear()

        while not self.stop_flag:
            sniff(filter="tcp and port 8000", prn=handle_packet, stop_filter=lambda x: self.stop_flag, count=1)