# Devil's Covert Channel

## Introduction

This project implements a covert communication channel to transmit hidden messages using TCP packet sizes. The goal is to send binary data covertly by encoding 2 bits of information per packet. The implementation uses a creative approach inspired by a puzzle called the "Devil's Chessboard," which allows for encoding and decoding of data based on bit manipulations and coin-flipping logic.

I first saw this puzzle in the 2016 issue of Matematik Dünyası, a Mathematics Magazine. It's a very tricky and fun puzzle to try to solve. If you want a full article about it, you can read more here: https://brianhamrick.com/blog/devils-chessboard

---

## Channel Capacity

The covert channel achieves a transmission rate of approximately 40 bits per second. This capacity allows for the transmission of short messages while maintaining stealth and reliability. The throughput is primarily limited by:
- The encoding of 2 bits per packet
- Network latency and packet transmission intervals
- Processing overhead for the Devil's Chessboard calculations

---

## Overview of the Devil's Chessboard Problem

*If you are already familiar with the Devil's Chessboard problem, you can skip this section.*

### Problem Statement

The devil has captured two people and is playing a game with them for their freedom. Person A will be presented with a chessboard with a penny in each square (64 total), with each penny either heads up or tails up randomly. The devil will choose a particular square and point it out to Person A. Person A then chooses a single square and flips the penny in that square. Afterward, Person A is sent away, and Person B is brought forward. Based on the new state of the board, Person B must point out the same square that the devil did to win their freedom. The two people can devise a strategy beforehand, but **cannot** communicate once the game starts.

### Solution

The solution leverages bitwise XOR operations. By numbering the coins from 0 to 63, the "value" of the chessboard is defined as the XOR of all indices where coins are heads up. Person A calculates which coin to flip such that the XOR value of the board matches the devil's chosen square. Since XOR is its own inverse, this ensures **Person B can always identify the square chosen by the devil**.

The game is winnable for any number of coins **n**, where  **n**  is a power of 2, due to the mathematical properties of hypercube graphs and their relationship to XOR operations.

---

## How This Problem is Used in Our Covert Channel

The Devil's Chessboard problem inspired the encoding strategy in this covert channel. We used this puzzle to send our encrypted messages. Our packets are maximum of 1024 bytes (representing 10 bits). The first 8 bits of this length represents chessboard and the last 2 bits are negation bits needed to resolve the bits sent in the receiver. (The usage of negation bits are explained later in this section)

```
Bit representation of packet size:

                    8 bits                        1 bit            1 bit
+-------------------------------------------+----------------+----------------+
| representation of chessboard with 8 coins | negation bit 1 | negation bit 2 |
+-------------------------------------------+----------------+----------------+

```

Lets explain the steps:

1. **Packet Size Constraints:**

   - Packets whose size is greater than 1500 bytes are splitted while sending. So we decided to limit the packet size to 1024 bytes, restricting the chessboard to 8 bits. 2 bits left are used to encryp and decrypt our 2 bit messages.

2. **Chessboard Representation:**
   - First 8 bit of bit representation of each packet's size is treated as a representation of a chessboard state.
   - A chessboard corresponds to an 8-bit binary, where each bit represents the state of a coin. `1` for heads up and `0` for heads down.

3. **Negation Bits:**
   - We create random chessboards and the solutions are random as well. So we had to use some bits to hide the information of how to use the solution to decrypt the hidden message.
   - The last two bits represent the negation bits. Since we encryp 2 bits every packet, we needed 2 bits at the end to resolve the bit in receiver. (The usage of negation bits are explained later in this section)

4. **Decoding the Message:**
   - The receiver first resolves the chessboard and negation bits from the packet size and gets devils numbers from the user parameters.
   - The receiver solves the problem and finds the coin to flip for every devils number.
   - The receiver finds the number of ones in the bit representation of the result.
   - The receiver uses negation bits to decode the message:
   
       #### Negation Bit Usage Table
    
        The negation bits are used to resolve the encoded message. The table below shows how the number of ones in the solution's bit representation and the negation bit determine the received message:
    
        | Number of Ones in Solution | Negation Bit | Received Message |
        |----------------------------|--------------|------------------|
        | 0                          | 0            | 0                |
        | 1                          | 0            | 1                |
        | 0                          | 1            | 1                |
        | 1                          | 1            | 0                |

By leveraging the mathematical properties of XOR and the Devil's Chessboard logic, this approach ensures reliable encoding and decoding of covert messages with minimal overhead.

---

### Encoding Process

1. Generate a random 8-bit chessboard.
2. Create devil's numbers using user parameters.
3. For each pair of devil's numbers and message bits:
   - Calculate the coin to flip based on the devil's chessboard.
   - Check the number of `1`s in the coin index's binary representation.
   - Determine if a negation bit is required.
4. Combine the chessboard and negation bits to calculate the packet size.

### Decoding Process

1. Extract the chessboard and negation bits from the received packet size.
2. Use the chessboard and devil's numbers to determine the coin to flip.
3. Reconstruct the message bit based on the coin's properties and the negation bit.
4. Repeat until the entire message is decoded.

---

## Example Walkthrough

1. **Sending a Message:**

   - Message bits to send: `01`
   - Random chessboard: `10110001`
   - Devil's numbers: `1`, `2` (The 2 parameters entered by the user were reduced to 0-7 by an algorithm to create devil's numbers.)

   **Calculation:**
   
   - XOR of table ( XOR of heads up coin indexes) is `110`
   - For devil's number `1`:
     - Coin to flip: `7` (binary: `111`, 3 ones)
     - Negation bit: `1` (odd number of ones does not align with message bit `0`).
   - For devil's number `2`:
     - Coin to flip: `4` (binary: `100`, 1 one)
     - Negation bit: `0` (odd number of ones aligns with message bit `1`).

   Packet size:
   `| chessboard: 10110011 | negation bits: 10 |`

2. **Receiving the Message:**

   Extract chessboard and negation bits:

   - Received chessboard: `10110001`
   - Received negation bits: `10`
   - Devil's numbers: `1`, `2`

   **Calculation:**
   
   *Negation bit usage table given can be used to understand better*
   - For devil's number `1`:
     - Coin to flip: `7` (binary: `111`, 3 ones)
     - Negation bit: `1`
     - Then since the binary representation has odd number of ones and the negation bit indicates that the message bit does not align with this oddness: The bit sent is `0`
   - For devil's number `2`:
     - Coin to flip: `4` (binary: `100`, 2 ones)
     - Negation bit: `0`
     - Then since the binary representation has even number of ones and the negation bit indicates that the message bit aligns with this oddness: The bit sent is `1`  

    Received message:
    - `01`

---

## Conclusion

This project showcases the creative use of the Devil's Chessboard problem to implement a covert communication channel. By encoding data into TCP packet sizes, it demonstrates an innovative way of transmitting hidden messages over a network. The design and implementation highlight the intersection of computer networks, cryptography, and problem-solving.
